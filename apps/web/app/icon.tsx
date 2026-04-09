export const size = {
  width: 32,
  height: 32
};

export const contentType = "image/svg+xml";

export default function Icon(): Response {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
      <defs>
        <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="#1ecbe1" />
          <stop offset="100%" stop-color="#ff9b35" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="8" fill="#0d1520" />
      <path d="M7 22h18" stroke="#c8d5e0" stroke-width="2" stroke-linecap="round" />
      <path d="M10 20V12M14 18V9M18 24V14M22 16V8" stroke="url(#g)" stroke-width="2.4" stroke-linecap="round" />
    </svg>
  `;

  return new Response(svg, {
    headers: {
      "Content-Type": contentType
    }
  });
}

