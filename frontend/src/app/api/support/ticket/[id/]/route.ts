import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

    console.log(`Forwarding status request for ticket ${id} to backend`);

    const response = await fetch(`${backendUrl}/api/support/ticket/${id}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      // Ensure we don't cache status lookups
      cache: 'no-store'
    });

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json({ detail: "Ticket not found" }, { status: 404 });
      }
      throw new Error(`Backend returned ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Error fetching ticket status:', error);
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    );
  }
}
