-- Wallet Database Schema for Supabase Integration
-- This schema properly integrates with Supabase's auth.users table

-- User wallets table - links to Supabase auth.users table
CREATE TABLE IF NOT EXISTS user_wallets (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE, -- Links to Supabase Users.uid
  balance DECIMAL(10,2) DEFAULT 0.00 NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Wallet transactions table - links to Supabase auth.users table
CREATE TABLE IF NOT EXISTS wallet_transactions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE, -- Links to Supabase Users.uid
  type VARCHAR(20) NOT NULL CHECK (type IN ('funding', 'usage')),
  amount DECIMAL(10,2) NOT NULL,
  payment_intent_id VARCHAR(255),
  status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'completed', 'failed')),
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_wallets_user_id ON user_wallets(user_id);
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_user_id ON wallet_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_created_at ON wallet_transactions(created_at DESC);

-- Row Level Security (RLS) policies
ALTER TABLE user_wallets ENABLE ROW LEVEL SECURITY;
ALTER TABLE wallet_transactions ENABLE ROW LEVEL SECURITY;

-- Policy for user_wallets - users can only see their own wallet
CREATE POLICY "Users can view own wallet" ON user_wallets
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own wallet" ON user_wallets
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own wallet" ON user_wallets
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy for wallet_transactions - users can only see their own transactions
CREATE POLICY "Users can view own transactions" ON wallet_transactions
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own transactions" ON wallet_transactions
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at on user_wallets
CREATE TRIGGER update_user_wallets_updated_at 
    BEFORE UPDATE ON user_wallets 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE user_wallets IS 'User wallet balances linked to Supabase auth.users';
COMMENT ON TABLE wallet_transactions IS 'Transaction history for user wallets';
COMMENT ON COLUMN user_wallets.user_id IS 'References auth.users(id) - the UID from Supabase Users table';
COMMENT ON COLUMN wallet_transactions.user_id IS 'References auth.users(id) - the UID from Supabase Users table';
COMMENT ON COLUMN wallet_transactions.type IS 'Type of transaction: funding (add money) or usage (spend money)';
COMMENT ON COLUMN wallet_transactions.amount IS 'Transaction amount in USD';
COMMENT ON COLUMN wallet_transactions.payment_intent_id IS 'Stripe payment intent ID for funding transactions';
COMMENT ON COLUMN wallet_transactions.status IS 'Transaction status: pending, completed, or failed';
