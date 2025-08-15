import React, { useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'

export const GoogleOneTap: React.FC = () => {
  const { initializeGoogleOneTap, user, loading } = useAuth()

  useEffect(() => {
    if (!user && !loading) {
      // Small delay to ensure the page is fully loaded
      const timer = setTimeout(() => {
        initializeGoogleOneTap()
      }, 1000)

      return () => clearTimeout(timer)
    }
  }, [user, loading, initializeGoogleOneTap])

  return null // This component doesn't render anything visible
}
