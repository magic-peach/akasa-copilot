'use client'

import { useState, useEffect } from 'react'
import { Plane, Mic, Calendar, MapPin, DollarSign, Clock, AlertTriangle } from 'lucide-react'

export default function AkasaCopilot() {
  const [isLoading, setIsLoading] = useState(false)
  const [flightData, setFlightData] = useState<any>(null)
  const [voiceActive, setVoiceActive] = useState(false)
  const [chatMessages, setChatMessages] = useState<any[]>([])

  // Test backend connection
  const testBackend = async () => {
    try {
      const response = await fetch('http://localhost:5000/health')
      const data = await response.json()
      console.log('Backend connected:', data)
    } catch (error) {
      console.error('Backend connection failed:', error)
    }
  }

  // Voice chat function
  const handleVoiceChat = async (message: string) => {
    setIsLoading(true)
    try {
      const response = await fetch('http://localhost:5000/chat/voice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'DEMO_USER',
          text_input: message
        })
      })
      
      const data = await response.json()
      setChatMessages(prev => [...prev, {
        user: message,
        assistant: data.response?.text || 'Sorry, I could not process your request.',
        timestamp: new Date().toISOString()
      }])
    } catch (error) {
      console.error('Voice chat error:', error)
    }
    setIsLoading(false)
  }

  // Get flight status
  const getFlightStatus = async (flightNumber: string) => {
    setIsLoading(true)
    try {
      const response = await fetch(`http://localhost:5000/flights/${flightNumber}/status`)
      const data = await response.json()
      setFlightData(data)
    } catch (error) {
      console.error('Flight status error:', error)
    }
    setIsLoading(false)
  }

  useEffect(() => {
    testBackend()
  }, [])

  return (
    <div className="min-h-screen bg-dark-900 text-white">
      {/* Header */}
      <header className="border-b border-dark-700 bg-dark-800/50 backdrop-blur-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Plane className="h-8 w-8 text-primary-500" />
              <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent">
                Akasa Copilot
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <button className="btn-secondary">Sign In</button>
              <button className="btn-primary">Sign Up</button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <h2 className="text-5xl font-bold mb-6 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
            Where are you flying to?
          </h2>
          <p className="text-xl text-gray-400 mb-8">
            AI-powered flight search with real-time risk assessment
          </p>
        </div>

        {/* Flight Search */}
        <div className="max-w-4xl mx-auto">
          <div className="card-glow p-8 mb-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium mb-2">From</label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="DEL"
                    className="input-field pl-10 w-full"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">To</label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="BOM"
                    className="input-field pl-10 w-full"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Date</label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                  <input
                    type="date"
                    className="input-field pl-10 w-full"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Budget</label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                  <input
                    type="number"
                    placeholder="5000"
                    className="input-field pl-10 w-full"
                  />
                </div>
              </div>
            </div>
            <button 
              className="btn-primary w-full"
              onClick={() => getFlightStatus('QP1001')}
              disabled={isLoading}
            >
              {isLoading ? 'Searching...' : 'Search Flights'}
            </button>
          </div>

          {/* Flight Results */}
          {flightData && (
            <div className="space-y-4">
              <h3 className="text-2xl font-bold mb-4">Available Flights</h3>
              <div className="flight-card">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-primary-500 rounded-lg flex items-center justify-center">
                      <Plane className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-lg">Akasa Air QP1001</h4>
                      <p className="text-gray-400">A320 • 2h 15m</p>
                    </div>
                  </div>
                  <div className="recommended-badge">
                    Recommended
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                  <div>
                    <p className="text-sm text-gray-400">Departure</p>
                    <p className="font-semibold">09:30 AM</p>
                    <p className="text-sm text-gray-400">DEL Terminal 3</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">Arrival</p>
                    <p className="font-semibold">11:45 AM</p>
                    <p className="text-sm text-gray-400">BOM Terminal 2</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">Price</p>
                    <p className="font-semibold text-2xl">₹4,800</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">Risk Score</p>
                    <div className="risk-badge-low">
                      Low Risk
                    </div>
                  </div>
                </div>
                
                <button className="btn-primary w-full">
                  Book Now
                </button>
              </div>
            </div>
          )}

          {/* Chat Messages */}
          {chatMessages.length > 0 && (
            <div className="card-glow p-6 mt-8">
              <h3 className="text-xl font-bold mb-4">AI Assistant</h3>
              <div className="space-y-4 max-h-64 overflow-y-auto">
                {chatMessages.map((msg, index) => (
                  <div key={index} className="space-y-2">
                    <div className="bg-primary-500/20 p-3 rounded-lg">
                      <p className="text-sm text-primary-400">You:</p>
                      <p>{msg.user}</p>
                    </div>
                    <div className="bg-dark-700 p-3 rounded-lg">
                      <p className="text-sm text-gray-400">Assistant:</p>
                      <p>{msg.assistant}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Voice Assistant Button */}
      <button
        className="voice-button"
        onClick={() => {
          const message = prompt('Ask me anything about your flight:')
          if (message) handleVoiceChat(message)
        }}
        disabled={isLoading}
      >
        <Mic className="h-6 w-6" />
      </button>

      {/* Demo Info */}
      <section className="container mx-auto px-6 py-8 border-t border-dark-700">
        <div className="text-center">
          <h3 className="text-xl font-bold mb-4">Demo Features</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card-glow p-6">
              <Mic className="h-8 w-8 text-primary-500 mx-auto mb-3" />
              <h4 className="font-semibold mb-2">Voice Assistant</h4>
              <p className="text-gray-400 text-sm">
                Ask about flight status, bookings, and get AI-powered responses
              </p>
            </div>
            <div className="card-glow p-6">
              <AlertTriangle className="h-8 w-8 text-yellow-500 mx-auto mb-3" />
              <h4 className="font-semibold mb-2">Risk Prediction</h4>
              <p className="text-gray-400 text-sm">
                ML-based disruption prediction with weather and historical data
              </p>
            </div>
            <div className="card-glow p-6">
              <Clock className="h-8 w-8 text-green-500 mx-auto mb-3" />
              <h4 className="font-semibold mb-2">Real-time Status</h4>
              <p className="text-gray-400 text-sm">
                Live flight tracking with gate information and delay alerts
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}