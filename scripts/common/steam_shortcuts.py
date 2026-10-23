#!/usr/bin/env python3
"""Manage non-Steam shortcuts through the running Steam client's CEF debug port
(127.0.0.1:8080, target SharedJSContext). No Steam restart needed. Stdlib only.
Adapted from Frame Control's frame/android/steam_shortcuts.py (MIT, (c) 2026 saphid).

  steam_shortcuts.py add NAME EXE START_DIR [ICON]   -> prints the shortcut app id
  steam_shortcuts.py list                            -> JSON [{appid, name}]
  steam_shortcuts.py remove APPID
  steam_shortcuts.py stop APPID
  steam_shortcuts.py gameid APPID                    -> the id for steam://rungameid/
"""
import base64, json, os, socket, struct, sys, urllib.request

DEVTOOLS = 'http://127.0.0.1:8080/json'
COLLECTION = "PC VR ports"


def target_ws():
    for t in json.load(urllib.request.urlopen(DEVTOOLS, timeout=5)):
        if t.get('title') == 'SharedJSContext':
            return t['webSocketDebuggerUrl']
    sys.exit('SharedJSContext not found: is the Steam client running?')


class WS:
    """Just enough RFC 6455 for one CDP request/response on loopback."""

    def __init__(self, url, timeout=20):
        host_port, path = url[len('ws://'):].split('/', 1)
        host, port = host_port.split(':')
        self.s = socket.create_connection((host, int(port)), timeout=timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f'GET /{path} HTTP/1.1\r\nHost: {host_port}\r\nUpgrade: websocket\r\n'
                        f'Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n'
                        'Sec-WebSocket-Version: 13\r\n\r\n').encode())
        buf = b''
        while b'\r\n\r\n' not in buf:
            buf += self.s.recv(4096)
        if b' 101 ' not in buf.split(b'\r\n', 1)[0]:
            sys.exit('websocket handshake failed')
        self.rest = buf.split(b'\r\n\r\n', 1)[1]

    def _read(self, n):
        while len(self.rest) < n:
            chunk = self.s.recv(65536)
            if not chunk:
                raise EOFError
            self.rest += chunk
        out, self.rest = self.rest[:n], self.rest[n:]
        return out

    def send(self, text):
        data = text.encode()
        mask = os.urandom(4)
        n = len(data)
        if n < 126:
            head = bytes([0x81, 0x80 | n])
        elif n < 65536:
            head = bytes([0x81, 0x80 | 126]) + struct.pack('>H', n)
        else:
            head = bytes([0x81, 0x80 | 127]) + struct.pack('>Q', n)
        self.s.sendall(head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv(self):
        msg = b''
        while True:
            b0, b1 = self._read(2)
            n = b1 & 0x7f
            if n == 126:
                n = struct.unpack('>H', self._read(2))[0]
            elif n == 127:
                n = struct.unpack('>Q', self._read(8))[0]
            msg += self._read(n)
            if b0 & 0x80:
                return msg.decode()


def evaluate(js, timeout=20):
    ws = WS(target_ws(), timeout)
    ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {
        'expression': js, 'awaitPromise': True, 'returnByValue': True}}))
    while True:
        r = json.loads(ws.recv())
        if r.get('id') == 1:
            break
    res = r.get('result', {})
    if 'exceptionDetails' in res:
        sys.exit('JS error: ' + json.dumps(res['exceptionDetails'])[:500])
    return res.get('result', {}).get('value')


def collection_js(appid, add):
    """Best-effort: put the app in (or take it out of) the user collection named COLLECTION."""
    return f'''async function syncCollection() {{
      try {{
        if (typeof collectionStore === "undefined") return "no collectionStore";
        const app = {{appid: {appid}}};
        const matches = collectionStore.GetUserCollectionsByName({json.dumps(COLLECTION)});
        let c = matches.find(x => !x.bIsDynamic && x.bAllowsDragAndDrop);
        if ({json.dumps(add)}) {{
          if (!c) c = collectionStore.NewUnsavedCollection({json.dumps(COLLECTION)}, undefined, [app]);
          else c.AsDragDropCollection().AddApps([app]);
          await collectionStore.SaveCollection(c);
        }} else if (c) {{
          c.AsDragDropCollection().RemoveApps([app]);
          await collectionStore.SaveCollection(c);
        }}
        return "ok";
      }} catch (e) {{ return "collection: " + String(e); }}
    }}'''


def main():
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == 'add':
        name, exe, start_dir = args[:3]
        icon = args[3] if len(args) > 3 else ''
        js = f'''(async () => {{
          const id = await SteamClient.Apps.AddShortcut({json.dumps(name)}, {json.dumps(exe)}, "", "");
          SteamClient.Apps.SetShortcutName(id, {json.dumps(name)});
          SteamClient.Apps.SetShortcutStartDir(id, {json.dumps(start_dir)});
          if ({json.dumps(icon)}) SteamClient.Apps.SetShortcutIcon(id, {json.dumps(icon)});
          if (typeof SteamClient.Apps.SetShortcutIsVR === "function") SteamClient.Apps.SetShortcutIsVR(id, true);
          {collection_js('id', True)}
          await syncCollection();
          return id;
        }})()'''
        print(evaluate(js))
    elif cmd == 'list':
        js = '''(async () => appStore.allApps.filter(a => a.app_type === 1073741824)
                  .map(a => ({appid: a.appid, name: a.display_name})))()'''
        print(json.dumps(evaluate(js)))
    elif cmd == 'remove':
        appid = int(args[0])
        js = f'''(async () => {{
          {collection_js(appid, False)}
          const w = await syncCollection();
          SteamClient.Apps.RemoveShortcut({appid});
          return w;
        }})()'''
        print(evaluate(js))
    elif cmd == 'stop':
        gid = (int(args[0]) << 32) | 0x02000000
        evaluate(f'SteamClient.Apps.TerminateApp({json.dumps(str(gid))}, false)')
        print('stopping')
    elif cmd == 'gameid':
        print((int(args[0]) << 32) | 0x02000000)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
