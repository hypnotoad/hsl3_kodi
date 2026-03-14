#
# hsl3_14587_kodi - kodi module for hsl3
#   Written by Ralf Dragon <hypnotoad@lindra.de>
#   Copyright (C) 2026 Ralf Dragon
#
# This program is freely distributable per the following license:
#
#  Permission to use, copy, modify, and distribute this software and its
#  documentation for any purpose and without fee is hereby granted,
#  provided that the above copyright notice appears in all copies and that
#  both that copyright notice and this permission notice appear in
#  supporting documentation.
#
#  I DISCLAIM ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING ALL
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL I
#  BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY
#  DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
#  WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION,
#  ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
#  SOFTWARE.

import json
import time
import threading
from hsl3_14587_module_loader import ModuleLoader


class LogicModule:
    def __init__(self, hsl3):
        self.fw = hsl3
        self.debug = self.fw.create_debug_section()
        self.wst = None
        self.player_id = 1
        self.rpc_id = 1
        self.rpc_handlers = {}
        self.state = {}

        self.notification_handlers = {
            "Application.OnVolumeChanged": self.on_notification_volume_changed,
            "Player.OnPause": self.on_notification_paused,
            "Player.OnPlay": self.on_notification_playing,
            "Player.OnPropertyChanged": self.on_notification_property_changed,
            "Player.OnResume": self.on_notification_playing,
            "Player.OnStop": self.on_notification_stopped,
            }

    def on_notification_playing(self, data=None):
        self.set_state("playing", 1)
        self.set_state("paused", 0)
        self.query_title()

    def on_notification_paused(self, data=None):
        self.set_state("playing", 0)
        self.set_state("paused", 1)

    def on_notification_stopped(self, data=None):
        self.set_state("playing", 0)
        self.set_state("paused", 0)
        self.set_state("title", '')
        self.set_state("album", '')
        self.set_state("artist", '')

    def on_notification_volume_changed(self, data):
        self.set_state("volume", int(data["volume"]))
        self.set_state("muted", int(data["muted"]))

    def on_notification_property_changed(self, data):
        property = data["property"]
        if "shuffled" in property:
            self.set_state("shuffled", int(property["shuffled"]))
        if "repeat" in property:
            self.set_state("repeated", int(property["repeat"] == "all"))

    def on_init(self, inputs, store):
        self.module_loader = ModuleLoader(self.fw)
        self.module_loader.load_zip("websocket",
                                    "websocket-client-1.9.0.zip",
                                    "/websocket-client-1.9.0")

        self.stop_event = threading.Event()
        self.start_thread(inputs)
        
    def on_calc(self, inputs):
        # execute rpc actions according to
        # https://kodi.wiki/view/JSON-RPC_API/v13

        # Use such that an action is carried out if None is returned (with 'not' or '!=')
        def kodi_state(output_key):
            if not output_key in self.state:
                return None
            else:
                return self.state[output_key]
            
        if inputs["server_name"].changed or inputs["port"].changed:
            self.debug.log("Reconnecting as connection parameters changed")
            if self.wst:
                self.stop_event.set()
                self.ws.close()
                self.wst.join()
                self.wst = None
                self.stop_event.clear()
            self.start_thread(inputs)

        if inputs["open_file"].changed:
            filename = inputs["open_file"].value.decode('utf8')
            self.exec_jrpc("Player.Open", {"item": {"file": filename}}, lambda x: self.query_player_id()) 
        
        if inputs["startstop"].changed:
            action = None
            if inputs["startstop"].value != 0:
                if not kodi_state("playing"):
                    action = "play"
            else:
                if kodi_state("paused") or kodi_state("playing") != False:
                    action = "stop"
            if action:
                self.exec_jrpc("Input.ExecuteAction", {"action": action}) 
        
        if inputs["pauseplay"].changed:
            play = None
            if inputs["pauseplay"].value != 0:
                if not kodi_state("paused"):
                    play = False
            else:
                if not kodi_state("playing"):
                    play = True
            if play is not None:
                self.exec_jrpc("Player.PlayPause", {"play" : play,
                                                    "playerid": self.player_id}) 
        
        if inputs["set_volume"].changed:
            volume = int(inputs["set_volume"].value)
            if volume != kodi_state("volume"):
                self.exec_jrpc("Application.SetVolume", {"volume": volume }) 

        if inputs["set_mute"].changed:
            mute = inputs["set_mute"].value != 0
            if mute != kodi_state("muted"):
                self.exec_jrpc("Application.SetMute", {"mute": mute}) 

        if inputs["nextprev"].changed:
            # unfortunately this creates a spike in the play status
            next = inputs["nextprev"].value != 0
            self.exec_jrpc("Player.GoTo", {"to": "next" if next else "previous",
                                           "playerid": self.player_id}) 
        
        if inputs["repeatall"].changed:
            repeat = inputs["repeatall"].value != 0
            if repeat != kodi_state("repeated"):
                self.exec_jrpc("Player.SetRepeat", {"repeat": "all" if repeat else "off",
                                                    "playerid": self.player_id}) 
        
        if inputs["shuffle"].changed:
            shuffle = inputs["shuffle"].value != 0
            if shuffle != kodi_state("shuffled"):
                self.exec_jrpc("Player.SetShuffle", {"shuffle": shuffle,
                                                     "playerid": self.player_id}) 
            
    def on_timer(self, timer):
        pass

    def set_state(self, key, value):
        # set output with sbc logic
        # - can be called from any thread
        # - encodes output to utf8 bytes, if not done yet
        if type(value) == str:
            value = value.encode("utf8")
        elif type(value) == bool:
            value = int(value)

        def set_sbc(self, key, value):    
            if not key in self.state or self.state[key] != value:
                self.fw.set_output(key, value)
            self.state[key] = value
        self.fw.run_in_context(set_sbc, (self, key, value))
        
    def exec_jrpc(self, method, params, rpc_handler=None):
        rpc = {"jsonrpc": "2.0",
               "method": method}
        if params is not None:
            rpc["params"] = params

        if rpc_handler is not None:
            rpc["id"] = self.rpc_id
            self.rpc_handlers[self.rpc_id] = rpc_handler
            self.rpc_id += 1

        #print("Sending jrpc: ", rpc)
        self.ws.send_text(json.dumps(rpc))

    def parse_jrpc(self, jrpc):
        if jrpc == '':
            return None
        try:
            obj = json.loads(jrpc)
        except ValueError:
            self.debug.log("ValueError parsing jrpc {}".format(jrpc))
            return None
        if 'error' in obj:
            self.debug.log("Jrpc error: {}".format(obj))
        return obj

    def query_player_id(self):
        # the id of the currently-playing player
        def handler(result):
            if len(result) != 0:
                # playing
                self.player_id = result[0]["playerid"]
                self.query_title()
            else:
                self.on_notification_stopped()
                
        self.exec_jrpc("Player.GetActivePlayers", None, handler)

    def query_title(self):
        def handler(result):
            if "item" in result:
                item = result["item"]
                self.set_state("current_file", item["file"])
                if "title" in item:
                    self.set_state("title", item["title"])
                if "album" in item:
                    self.set_state("album", item["album"])
                if "artist" in item:
                    self.set_state("artist", ', '.join(item["artist"]))
        self.exec_jrpc("Player.GetItem", {"playerid": self.player_id,
                                          "properties": ["title", "album", "artist", "file"]},
                       handler)

    def query_state(self):
        def player_handler(result):
            self.set_state("shuffled", result["shuffled"])
            self.set_state("repeated", result["repeat"] != "off")
            self.set_state("playing", result["speed"] != 0)
            self.set_state("paused", result["speed"] == 0)
        self.exec_jrpc("Player.GetProperties", {"playerid": self.player_id,
                                                "properties": ["repeat", "shuffled", "speed"]},
                       player_handler)

        def application_handler(result):
            self.set_state("volume", result["volume"])
            self.set_state("muted", int(result["muted"]))
        self.exec_jrpc("Application.GetProperties", {"properties": ["volume", "muted"]},
                       application_handler)
        
    def on_open(self, ws):
        self.set_state("connected", 1)
        self.query_player_id()
        self.query_state()

    def on_message(self, ws, message):
        #self.debug.log("Received: {}".format(message))
        response = self.parse_jrpc(message)
        if response is None:
            return

        if 'result' in response and 'id' in response:
            result = response["result"]
            rpc_id = response["id"]
            if rpc_id not in self.rpc_handlers:
                self.debug.log("Unknown reponse data: {}".format(response))
                return
            self.rpc_handlers[rpc_id](result)
            self.rpc_handlers.pop(rpc_id)
            
        if not 'method' in response:
            return

        method = response['method']
        if method in self.notification_handlers:
            data = response['params']["data"] if 'params' in response else None
            if "player" in data:
                self.player_id = data["player"]["playerid"]
            self.notification_handlers[method](data)

    def on_error(self, ws, exception):
        self.debug.log("Error: '{}'".format(exception))
    
    def on_close(self, ws, code, msg):
        self.debug.log("Closing with code {}: {}".format(code, msg))
        self.set_state("connected", 0)

    def on_reconnect(self, ws):
        self.set_state("connected", 1)

    def start_thread(self, inputs):
        ws_url = "ws://{}:{}".format(inputs["server_name"].value.decode('ascii'),
                                     inputs["port"].value)
        self.debug.log("Connecting to {}".format(ws_url))

        import websocket
        #websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(ws_url,
                                         on_open=self.on_open,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close,
                                         on_reconnect=self.on_reconnect)

        # Start a background thread to run the WebSocket client
        def connect():
            while True:
                self.ws.run_forever(ping_timeout=5,
                                    ping_interval=10,
                                    ping_payload="JSONRPC.Ping")
                if self.stop_event.is_set():
                    break
                time.sleep(10)
                
        self.wst = threading.Thread(target=connect)
        self.wst.daemon = True
        self.wst.start()

        # Ugly! To avoid using the websocket before it is connected
        time.sleep(1)


