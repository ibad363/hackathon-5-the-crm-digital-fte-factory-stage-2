import { NextRequest, NextResponse } from 'next/server';

interface SupportFormData {
  name: string;
  email: string;
  subject: string;
  category: string;
  priority: string;
  message: string;
}

export async function POST(request: NextRequest) {
  try {
    const body: SupportFormData = await request.json();

    // Validate required fields
    const requiredFields = ['name', 'email', 'subject', 'category', 'message'];
    for (const field of requiredFields) {
      if (!body[field as keyof SupportFormData]) {
        return NextResponse.json(
          { detail: `Missing required field: ${field}` },
          { status: 400 }
        );
      }
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(body.email)) {
      return NextResponse.json(
        { detail: 'Invalid email format' },
        { status: 400 }
      );
    }

    // Forward request to FastAPI backend
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

    console.log(`Forwarding request to backend at ${backendUrl}/api/support/submit`);

    const backendResponse = await fetch(`${backendUrl}/api/support/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: body.name,
        email: body.email,
        subject: body.subject,
        message: body.message,
        category: body.category,
        priority: body.priority
      }),
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.text();
      console.error('Backend returned error:', backendResponse.status, errorData);
      throw new Error(`Backend error: ${backendResponse.status}`);
    }

    const backendData = await backendResponse.json();

    console.log('Support ticket created on backend:', {
      ticket_id: backendData.ticket_id,
    });

    // Return success response with ticket ID from backend
    return NextResponse.json({
      success: true,
      ticket_id: backendData.ticket_id,
      message: backendData.message,
      estimated_response_time: backendData.estimated_response_time
    });

  } catch (error) {
    console.error('Error processing support request:', error);
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    );
  }
}
