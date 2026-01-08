import http from 'k6/http';
import { sleep } from 'k6';


const TOTAL_RPS = 400;
const DURATION = '10m';

function rate(percentage) {
    return TOTAL_RPS * percentage;
}

function getRandomInt(min, max) {
    min = Math.ceil(min);
    max = Math.floor(max);
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

export const options = {
    scenarios: {
        read_endpoint: {
            exec: 'read',
            executor: 'constant-arrival-rate',
            duration: DURATION,
            rate: rate(0.9),
            timeUnit: '1s',
            preAllocatedVUs: 50,
            maxVUs: 100,
        },
        write_endpoint: {
            exec: 'write',
            executor: 'constant-arrival-rate',
            duration: DURATION,
            rate: rate(0.1),
            timeUnit: '1s',
            preAllocatedVUs: 50,
            maxVUs: 100,
        },
    },
};

export function read() {
    http.get(`http://localhost:8080/read?percent=20&id=${getRandomInt(0, 9999)}`);
    sleep(0.01);
}

export function write() {
    http.post(`http://localhost:8080/write?data=test`);
    sleep(0.01);
}