import { NextRequest, NextResponse } from 'next/server';

interface SupportFormData {
  name: string;
  email: string;
  subject: string;
  category: string;
  priority: string;
  message: string;
}

// Generate a unique ticket ID
function generateTicketId(): string {
  const timestamp = Date.now().toString(36).toUpperCase();
  const random = Math.random().toString(36).substring(2, 6).toUpperCase();
  return `TKT-${timestamp}-${random}`;
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

    // Generate ticket ID
    const ticketId = generateTicketId();

    // TODO: In production, this would:
    // 1. Store the ticket in PostgreSQL database
    // 2. Publish to Kafka topic (fte.tickets.incoming)
    // 3. Trigger the AI agent for processing

    console.log('Support ticket created:', {
      ticket_id: ticketId,
      ...body,
      created_at: new Date().toISOString(),
      channel: 'web_form'
    });

    // Return success response with ticket ID
    return NextResponse.json({
      success: true,
      ticket_id: ticketId,
      message: 'Support request submitted successfully',
      estimated_response_time: '5 minutes'
    });

  } catch (error) {
    console.error('Error processing support request:', error);
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    );
  }
}
