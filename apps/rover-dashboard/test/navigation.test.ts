import {it,expect} from 'vitest';
import {readFileSync} from 'node:fs';
import {NAV} from '../../../packages/protocol/index';
import {sample} from '../../rover-bridge/test/fixtures';
import {navigationDetail,sensorValid} from '../src/navigation';

it('explains every actual firmware navigation phase and masks absent decisions',()=>{
 for(const nav of NAV)expect(navigationDetail({...sample,nav},true)).not.toMatch(/Unknown firmware/);
 expect(navigationDetail(null,false)).toContain('unknown');expect(navigationDetail(sample,false)).not.toContain('Operator hold');
 expect(navigationDetail({...sample,nav:'SETTLE'},true)).toContain('ties left');
 expect(navigationDetail({...sample,nav:'TURNING'},true)).toContain('540 ms');
 expect(navigationDetail({...sample,nav:'REASSESS'},true)).toContain('new sample from every sensor');
});
it('display thresholds and timing remain tied to the unchanged C++ firmware',()=>{
 const source=readFileSync('include/rover_control.h','utf8');
 for(const value of ['MANUAL_MS = 1200','FRESH_MS = 500','SETTLE_MS = 180','TURN_MS = 540','NEUTRAL_MS = 100','MAX_TURN_ATTEMPTS = 3','BLOCK_CM = 35','CLEAR_CM = 45','SIDE_STOP_CM = 20'])expect(source).toContain(value);
 for(const name of NAV)expect(source).toContain('"'+name+'"');
 expect(source).toContain('left >= right ? Motion::Left : Motion::Right');
});
it('invalid ranges and expired samples never display as clear distances',()=>{
 expect(sensorValid({...sample,cm:[-1,100,70]},0,0)).toBe(false);expect(sensorValid({...sample,age:[500,0,0]},0,0)).toBe(true);expect(sensorValid({...sample,age:[500,0,0]},0,1)).toBe(false);expect(sensorValid(sample,0,100)).toBe(true);
});
