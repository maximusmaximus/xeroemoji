"""Interop check with the official MCP Python SDK (optional; needs `pip install mcp`).
   python3 mcp/tests/sdk_client_check.py"""
import asyncio, json, os, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'server.py')

async def main():
    async with stdio_client(StdioServerParameters(command=sys.executable, args=[SERVER])) as (r, w):
        async with ClientSession(r, w) as s:
            init = await s.initialize()
            tools = await s.list_tools()
            res = await s.call_tool('get_emoji', {'emoji': '🧑🏽‍🚀'})
            out = json.loads(res.content[0].text)
            v = await s.call_tool('get_skin_tone_variants', {'emoji': '👋'})
            si = getattr(init, 'server_info', None) or init.serverInfo          # SDK 2.x snake_case, 1.x camelCase
            pv = getattr(init, 'protocol_version', None) or init.protocolVersion
            print('server', si.name, si.version, 'protocol', pv)
            print('tools', sorted(t.name for t in tools.tools))
            print('get_emoji ->', out['file'], out['svg_url'])
            print('variants ->', json.loads(v.content[0].text)['count'])
            assert out['file'] == '1f9d1-1f3fd-200d-1f680' and not (getattr(res, 'is_error', None) or getattr(res, 'isError', False))
            print('SDK interop OK')

asyncio.run(main())
