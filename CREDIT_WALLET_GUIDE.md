# Manual Wallet Credit Guide

Since we're using the payment link method, you need to manually credit user wallets after successful payments.

## How to Credit a Wallet

### Method 1: Using the API Endpoint (by User ID)

When a payment succeeds, call the credit endpoint:

```bash
curl -X POST http://your-domain/api/wallet/credit \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_uuid_here",
    "amount": 25.00,
    "payment_reference": "payment_id_from_stripe"
  }'
```

### Method 1b: Using the API Endpoint (by Email) - EASIER!

Credit a wallet using the user's email address:

```bash
curl -X POST http://your-domain/api/wallet/credit-by-email \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "amount": 25.00,
    "payment_reference": "payment_id_from_stripe"
  }'
```

**Response:**
```json
{
  "success": true,
  "user_id": "user_uuid",
  "email": "user@example.com",
  "new_balance": 25.00,
  "message": "Wallet credited successfully"
}
```

### Method 2: Using Supabase Dashboard

1. Go to your Supabase dashboard
2. Navigate to Table Editor
3. Find the `user_wallets` table
4. Find the user's record by `user_id`
5. Update the `balance` field
6. Add a record to `wallet_transactions` table

### Method 3: Direct SQL (for admins)

```sql
-- Update user's wallet balance
UPDATE user_wallets 
SET balance = balance + 25.00, 
    updated_at = NOW() 
WHERE user_id = 'user_uuid_here';

-- Add transaction record
INSERT INTO wallet_transactions (
  user_id, 
  type, 
  amount, 
  payment_intent_id, 
  status, 
  description, 
  created_at
) VALUES (
  'user_uuid_here',
  'funding',
  25.00,
  'payment_reference_here',
  'completed',
  'Wallet funded with $25.00',
  NOW()
);
```

## Finding User ID

To find a user's ID, you can:

1. **From Stripe Dashboard**: Check the customer email in the payment
2. **From Supabase Dashboard**: Go to Authentication > Users and find by email
3. **From your app**: Check the user's session or profile

## Payment Reference

The `payment_intent_id` field should contain:
- Stripe payment intent ID (if available)
- Order number
- Or any unique identifier for the payment

## Example Workflow

1. **User makes payment** via your Stripe payment link
2. **You get notified** (email, Stripe dashboard, etc.)
3. **Find the user** by email or payment details
4. **Credit their wallet** using one of the methods above
5. **User sees updated balance** in your app

## Automation Options

### Option A: Stripe Webhook (Advanced)
If you want automation, you can set up a Stripe webhook to automatically credit wallets when payments succeed.

### Option B: Admin Dashboard
Create a simple admin interface to credit wallets by email/amount.

### Option C: Email Integration
Parse payment confirmation emails to automatically credit wallets.

## Testing

To test the credit system:

1. Find a test user's ID
2. Call the credit API with a small amount
3. Verify the balance updates in your app
4. Check the transaction history

## Troubleshooting

- **"User ID not found"**: Check if the user exists in Supabase auth.users
- **"Balance not updating"**: Check if the user has a wallet record (one will be created automatically)
- **"Permission denied"**: Make sure you're using the service key for admin operations
