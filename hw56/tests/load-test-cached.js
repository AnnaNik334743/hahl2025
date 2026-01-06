import http from 'k6/http';

export const options = {
  scenarios: {
    constant_800: {
      executor: 'constant-arrival-rate',
      rate: 800,
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 200,
      maxVUs: 500,
    }
  }
};

const BASE_URL = 'http://localhost:8080';

function getRandomMonth() {
  return Math.floor(Math.random() * 12) + 1;
}

function getRandomDay() {
  return Math.floor(Math.random() * 31) + 1;
}

function getRandomHour() {
  return Math.floor(Math.random() * 24) + 1;
}

export default function () {
  const randomMonth = getRandomMonth();
  const randomDay = getRandomDay();
  const randomHour = getRandomHour();
  const endpoint = `/holidays/${randomMonth}/${randomDay}/${randomHour}/cached`;
  const response = http.get(`${BASE_URL}${endpoint}`);
}