import http from "k6/http";

const TOTAL_RPS = 40;

function rate(percentage) {
  return TOTAL_RPS * percentage;
}

export const options = {
  scenarios: {
    async_endpoint: {
      exec: "async",
      executor: "constant-arrival-rate",
      duration: "10m",
      rate: rate(0.65),
      timeUnit: "1s",
      preAllocatedVUs: 50,
      maxVUs: 100,
    },
    sync_endpoint: {
      exec: "sync",
      executor: "constant-arrival-rate",
      duration: "10m",
      rate: rate(0.35),
      timeUnit: "1s",
      preAllocatedVUs: 50,
      maxVUs: 100,
    },
  },
};

export function async() {
  http.get("http://localhost:8081/app/async");
}

export function sync() {
  http.get("http://localhost:8081/app/sync");
}