import React, { useEffect, useRef } from 'react'
import { useAuth } from '../contexts/AuthContext'

interface GoogleSignInButtonProps {
  className?: string
  theme?: 'outline' | 'filled_blue' | 'filled_black'
  size?: 'large' | 'medium' | 'small'
  text?: 'signin_with' | 'signup_with' | 'continue_with' | 'signin'
  shape?: 'rectangular' | 'rounded' | 'pill'
  logoAlignment?: 'left' | 'center'
}

export const GoogleSignInButton: React.FC<GoogleSignInButtonProps> = ({
  className = '',
  theme = 'outline',
  size = 'large',
  text = 'signin_with',
  shape = 'rectangular',
  logoAlignment = 'left'
}) => {
  const buttonRef = useRef<HTMLDivElement>(null)
  const { user, loading } = useAuth()

  useEffect(() => {
    if (buttonRef.current && window.google && !user && !loading) {
      window.google.accounts.id.renderButton(buttonRef.current, {
        type: 'standard',
        theme,
        size,
        text,
        shape,
        logo_alignment: logoAlignment,
        width: buttonRef.current.offsetWidth || (size === 'medium' ? 96 : 112) // Smaller width for medium size
      })
    }
  }, [user, loading, theme, size, text, shape, logoAlignment])

  if (user) {
    return null // Don't show button if user is signed in
  }

  return (
    <div 
      ref={buttonRef} 
      className={`${className} overflow-hidden`}
      style={{ 
        minHeight: size === 'large' ? '40px' : size === 'medium' ? '32px' : '28px',
        maxWidth: '100%'
      }}
    />
  )
}
