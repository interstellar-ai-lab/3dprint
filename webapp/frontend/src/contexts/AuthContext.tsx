import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { supabase, User, AuthState } from '../lib/supabase'

// TypeScript declarations for Google One Tap
declare global {
  interface Window {
    google: {
      accounts: {
        id: {
          initialize: (config: any) => void
          prompt: () => void
          renderButton: (element: HTMLElement, config: any) => void
        }
      }
    }
  }
}

interface AuthContextType extends AuthState {
  signInWithGoogle: () => Promise<void>
  signOut: () => Promise<void>
  refreshUser: () => Promise<void>
  initializeGoogleOneTap: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = async () => {
    try {
      const { data: { user: supabaseUser } } = await supabase.auth.getUser()
      
      if (supabaseUser) {
        setUser({
          id: supabaseUser.id,
          email: supabaseUser.email || '',
          user_metadata: supabaseUser.user_metadata
        })
      } else {
        setUser(null)
      }
    } catch (error) {
      console.error('Error refreshing user:', error)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const signInWithGoogle = async () => {
    try {
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`
        }
      })
      
      if (error) throw error
    } catch (error) {
      console.error('Error signing in with Google:', error)
      throw error
    }
  }

  const signOut = async () => {
    try {
      await supabase.auth.signOut()
      setUser(null)
    } catch (error) {
      console.error('Error signing out:', error)
    }
  }

  const initializeGoogleOneTap = useCallback(async () => {
    try {
      // Check if user is already signed in
      const { data: { session } } = await supabase.auth.getSession()
      if (session?.user) {
        setUser({
          id: session.user.id,
          email: session.user.email || '',
          user_metadata: session.user.user_metadata
        })
        setLoading(false)
        return
      }

      // Initialize Google One Tap
      if (window.google) {
        window.google.accounts.id.initialize({
          client_id: '1029338250413-7egddb2815bdnrv24o61gdcejm04bf71.apps.googleusercontent.com',
          callback: async (response: any) => {
            try {
              // Sign in with ID token
              const { data, error } = await supabase.auth.signInWithIdToken({
                provider: 'google',
                token: response.credential,
              })

              if (error) throw error

              if (data.user) {
                setUser({
                  id: data.user.id,
                  email: data.user.email || '',
                  user_metadata: data.user.user_metadata
                })
              }
            } catch (error) {
              console.error('Error handling Google sign-in:', error)
            }
          },
          use_fedcm_for_prompt: true, // For Chrome's third-party cookie phase-out
        })

        // Show One Tap UI
        window.google.accounts.id.prompt()
      }
    } catch (error) {
      console.error('Error initializing Google One Tap:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshUser()
  }, [])

  const value: AuthContextType = {
    user,
    loading,
    signInWithGoogle,
    signOut,
    refreshUser,
    initializeGoogleOneTap
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
