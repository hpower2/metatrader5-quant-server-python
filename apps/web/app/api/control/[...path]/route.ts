import { NextRequest, NextResponse } from "next/server";

const CONTROL_API_URL = process.env.QUANT_API_URL ?? "http://quant-api:8010";

async function proxy(request: NextRequest, method: "GET" | "POST") {
  const path = request.nextUrl.pathname.replace("/api/control", "");
  const search = request.nextUrl.search;
  const target = `${CONTROL_API_URL}${path}${search}`;
  const init: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json"
    },
    cache: "no-store"
  };

  if (method === "POST") {
    init.body = await request.text();
  }

  const response = await fetch(target, init);

  const text = await response.text();

  return new NextResponse(text, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") ?? "application/json"
    }
  });
}

export async function GET(request: NextRequest) {
  return proxy(request, "GET");
}

export async function POST(request: NextRequest) {
  return proxy(request, "POST");
}
