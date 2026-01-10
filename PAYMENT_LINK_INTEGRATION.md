# Frontend Integration - Payment Link Flow

## Workshop Registration with UPI Payment Link

### Step 1: Update API Client

```typescript
// lib/api/client.ts

async createWorkshopPaymentLink(
  workshopId: string,
  registration: WorkshopRegistrationRequest
): Promise<{ payment_link_id: string; short_url: string; amount: number; reference_id: string }> {
  return this.request(`/api/workshops/${workshopId}/create-payment-link`, {
    method: "POST",
    body: JSON.stringify(registration),
  });
}
```

### Step 2: Workshop Registration Page

```typescript
// app/workshops/[slug]/page.tsx

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();

  try {
    setSubmitting(true);

    const registrationData: WorkshopRegistrationRequest = {
      name: formData.name,
      email: formData.email,
      phone: formData.phone.replace(/\D/g, ''),
      year: formData.year,
      college_name: formData.collegeName,
      referral_id: formData.referralId || undefined,
    };

    // Create payment link
    const response = await api.createWorkshopPaymentLink(workshopSlug, registrationData);
    
    // Redirect to payment link
    window.location.href = response.short_url;
    
  } catch (error) {
    console.error('Error creating payment link:', error);
    alert(error instanceof Error ? error.message : 'Failed to create payment link');
  } finally {
    setSubmitting(false);
  }
};
```

### Step 3: Payment Success Page

```typescript
// app/workshops/[slug]/payment-success/page.tsx

'use client';

import { useEffect, useState } from 'react';
import { useParams, useSearchParams, useRouter } from 'next/navigation';
import PageSection from '@/components/_core/layout/PageSection';

export default function PaymentSuccessPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const workshopSlug = params?.slug as string;

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const verifyPayment = async () => {
      try {
        // Get callback parameters
        const payment_link_id = searchParams.get('payment_link_id');
        const payment_link_reference_id = searchParams.get('payment_link_reference_id');
        const payment_link_status = searchParams.get('payment_link_status');
        const razorpay_payment_id = searchParams.get('razorpay_payment_id');
        const razorpay_signature = searchParams.get('razorpay_signature');

        if (!payment_link_id || !payment_link_reference_id || !payment_link_status) {
          setStatus('error');
          setMessage('Invalid payment callback');
          return;
        }

        // Call backend callback endpoint
        const response = await fetch(
          `/api/workshops/${workshopSlug}/payment-callback?` +
          new URLSearchParams({
            payment_link_id,
            payment_link_reference_id,
            payment_link_status,
            ...(razorpay_payment_id && { razorpay_payment_id }),
            ...(razorpay_signature && { razorpay_signature }),
          }),
          {
            headers: {
              Authorization: `Bearer ${await auth.currentUser?.getIdToken()}`,
            },
          }
        );

        const data = await response.json();

        if (data.status === 'success') {
          setStatus('success');
          setMessage('Registration confirmed! Check your email for details.');
          
          // Redirect to dashboard after 3 seconds
          setTimeout(() => {
            router.push('/dashboard');
          }, 3000);
        } else {
          setStatus('error');
          setMessage(data.message || 'Payment verification failed');
        }
      } catch (error) {
        console.error('Error verifying payment:', error);
        setStatus('error');
        setMessage('Failed to verify payment');
      }
    };

    verifyPayment();
  }, [workshopSlug, searchParams, router]);

  return (
    <PageSection title="Payment Status" className="min-h-screen">
      <div className="max-w-2xl mx-auto text-center">
        {status === 'loading' && (
          <div>
            <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-red-600 mx-auto mb-4"></div>
            <p className="text-gray-400">Verifying payment...</p>
          </div>
        )}

        {status === 'success' && (
          <div className="bg-green-950/30 border border-green-600/50 rounded-2xl p-8">
            <div className="text-6xl mb-4">✓</div>
            <h2 className="text-3xl font-bold text-green-400 mb-4">Payment Successful!</h2>
            <p className="text-gray-300 mb-6">{message}</p>
            <p className="text-sm text-gray-500">Redirecting to dashboard...</p>
          </div>
        )}

        {status === 'error' && (
          <div className="bg-red-950/30 border border-red-600/50 rounded-2xl p-8">
            <div className="text-6xl mb-4">✗</div>
            <h2 className="text-3xl font-bold text-red-400 mb-4">Payment Failed</h2>
            <p className="text-gray-300 mb-6">{message}</p>
            <button
              onClick={() => router.push(`/workshops/${workshopSlug}`)}
              className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </PageSection>
  );
}
```

### Step 4: Update API Types

```typescript
// lib/api/types.ts

export interface CreatePaymentLinkResponse {
  payment_link_id: string;
  short_url: string;
  amount: number;
  reference_id: string;
}
```

## Payment Flow

1. **User fills registration form** → Submits
2. **Backend creates payment link** → Returns `short_url`
3. **Frontend redirects to payment link** → User pays via UPI/Card/NetBanking
4. **Razorpay redirects back** → `/workshops/{slug}/payment-success?payment_link_id=...&payment_link_status=paid`
5. **Frontend calls callback endpoint** → Backend verifies signature
6. **Backend creates registration** → Sends confirmation email
7. **Frontend shows success** → Redirects to dashboard

## Webhook Events

Configure in Razorpay Dashboard:
- `payment_link.paid` - Payment successful
- `payment_link.cancelled` - User cancelled
- `payment_link.expired` - Link expired

## Testing

### Test Payment Link
```bash
# Create payment link
curl -X POST http://localhost:8000/api/workshops/ai-ml-workshop/create-payment-link \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "phone": "9876543210",
    "year": "3rd Year",
    "college_name": "Test College"
  }'

# Response
{
  "payment_link_id": "plink_xxxxx",
  "short_url": "https://rzp.io/i/xxxxx",
  "amount": 500,
  "reference_id": "ai-ml-workshop_1234567890"
}
```

### Test Callback
```bash
# Simulate callback
curl "http://localhost:8000/api/workshops/ai-ml-workshop/payment-callback?payment_link_id=plink_xxxxx&payment_link_reference_id=ai-ml-workshop_1234567890&payment_link_status=paid&razorpay_payment_id=pay_xxxxx&razorpay_signature=xxxxx" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Advantages of Payment Links

✅ **No frontend integration** - Just redirect to URL
✅ **UPI support** - Native UPI apps, QR code, UPI ID
✅ **Multiple payment methods** - Cards, NetBanking, Wallets
✅ **SMS/Email notifications** - Automatic reminders
✅ **Mobile optimized** - Better UX on mobile
✅ **Expiry handling** - Auto-expire after 24 hours
✅ **Partial payments** - Optional (disabled in our case)
