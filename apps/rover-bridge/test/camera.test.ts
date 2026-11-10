import {EventEmitter} from 'node:events';
import {PassThrough} from 'node:stream';
import http from 'node:http';
import {afterEach,it,expect,vi} from 'vitest';
import {proxyCamera} from '../src/camera';
import type {Request,Response} from 'express';
afterEach(()=>vi.restoreAllMocks());
function mockCamera(code=200,type='image/jpeg'){
 const source=new PassThrough() as PassThrough&{statusCode:number;headers:Record<string,string>};source.statusCode=code;source.headers={'content-type':type};
 const upstream=Object.assign(new EventEmitter(),{destroy:vi.fn(),end:()=>{}});
 vi.spyOn(http,'request').mockImplementation(((_opts:unknown,cb:(v:unknown)=>void)=>{queueMicrotask(()=>cb(source));return upstream;}) as typeof http.request);
 const response=Object.assign(new PassThrough(),{headersSent:false,status:vi.fn(),json:vi.fn(),setHeader:vi.fn()});response.status.mockReturnValue(response);
 return {source,upstream,response};
}
it('proxies genuine JPEG and multipart streams, closes camera when viewer disconnects',async()=>{
 const {source,upstream,response}=mockCamera();let data='';response.on('data',b=>data+=b.toString());proxyCamera('192.168.50.20','snapshot',{query:{}} as Request,response as unknown as Response);await Promise.resolve();source.end('JPEG-MOCK');await new Promise(r=>setTimeout(r,5));expect(data).toBe('JPEG-MOCK');expect(response.setHeader).toHaveBeenCalledWith('Content-Type','image/jpeg');response.emit('close');expect(upstream.destroy).toHaveBeenCalled();
});
it.each([[503,'text/plain'],[200,'text/html']])('rejects camera status/type failure %i %s',async(code,type)=>{
 const {response}=mockCamera(code,type);proxyCamera('192.168.50.20','snapshot',{query:{}} as Request,response as unknown as Response);await Promise.resolve();expect(response.status).toHaveBeenCalledWith(502);expect(response.json).toHaveBeenCalledWith(expect.objectContaining({error:expect.stringContaining('Camera unavailable')}));
});
it('network errors and stalled camera reads fail explicitly',async()=>{
 const {upstream,response}=mockCamera();proxyCamera('192.168.50.20','status',{query:{}} as Request,response as unknown as Response);upstream.emit('error',Error('Wi-Fi disconnected'));expect(response.status).toHaveBeenCalledWith(502);upstream.emit('timeout');expect(upstream.destroy).toHaveBeenCalled();await Promise.resolve();
});
