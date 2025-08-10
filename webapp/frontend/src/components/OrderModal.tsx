import React, { useState, useEffect } from 'react';

interface OrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  modelName: string;
  modelImage: string;
}

interface ShippingAddress {
  fullName: string;
  email: string;
  address: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
}

interface PaymentInfo {
  cardNumber: string;
  expiryDate: string;
  cvv: string;
  nameOnCard: string;
}

export const OrderModal: React.FC<OrderModalProps> = ({ isOpen, onClose, modelName, modelImage }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [orderProcessing, setOrderProcessing] = useState(false);
  const [orderComplete, setOrderComplete] = useState(false);
  
  const [shippingAddress, setShippingAddress] = useState<ShippingAddress>({
    fullName: '',
    email: '',
    address: '',
    city: '',
    state: '',
    zipCode: '',
    country: 'United States'
  });

  const [paymentInfo, setPaymentInfo] = useState<PaymentInfo>({
    cardNumber: '',
    expiryDate: '',
    cvv: '',
    nameOnCard: ''
  });

  const [printOptions, setPrintOptions] = useState({
    material: 'PLA',
    color: 'White',
    quality: 'Standard',
    infill: '15%',
    quantity: 1
  });

  const basePrice = 49.99;
  const materialPrices = { PLA: 0, ABS: 5, PETG: 8, TPU: 12 };
  const qualityPrices = { Draft: -10, Standard: 0, High: 15, Ultra: 30 };
  
  const calculatePrice = () => {
    const materialCost = materialPrices[printOptions.material as keyof typeof materialPrices] || 0;
    const qualityCost = qualityPrices[printOptions.quality as keyof typeof qualityPrices] || 0;
    const subtotal = (basePrice + materialCost + qualityCost) * printOptions.quantity;
    const shipping = 9.99;
    const tax = subtotal * 0.08;
    return {
      subtotal: subtotal.toFixed(2),
      shipping: shipping.toFixed(2),
      tax: tax.toFixed(2),
      total: (subtotal + shipping + tax).toFixed(2)
    };
  };

  const handleNextStep = () => {
    setCurrentStep(prev => prev + 1);
  };

  const handlePrevStep = () => {
    setCurrentStep(prev => prev - 1);
  };

  const handleSubmitOrder = async () => {
    setOrderProcessing(true);
    
    // Simulate payment processing
    setTimeout(() => {
      setOrderProcessing(false);
      setOrderComplete(true);
    }, 3000);
  };

  const resetModal = () => {
    setCurrentStep(1);
    setOrderProcessing(false);
    setOrderComplete(false);
    setShippingAddress({
      fullName: '',
      email: '',
      address: '',
      city: '',
      state: '',
      zipCode: '',
      country: 'United States'
    });
    setPaymentInfo({
      cardNumber: '',
      expiryDate: '',
      cvv: '',
      nameOnCard: ''
    });
  };

  // Prevent body scroll when modal is open and handle escape key
  useEffect(() => {
    if (isOpen) {
      // Store original overflow value
      const originalOverflow = document.body.style.overflow;
      // Prevent scrolling
      document.body.style.overflow = 'hidden';
      
      // Handle escape key
      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          resetModal();
          onClose();
        }
      };
      
      document.addEventListener('keydown', handleEscape);
      
      // Cleanup function to restore original overflow and remove event listener
      return () => {
        document.body.style.overflow = originalOverflow;
        document.removeEventListener('keydown', handleEscape);
      };
    }
  }, [isOpen, onClose]);

  const handleClose = () => {
    resetModal();
    onClose();
  };

  const handleModalClick = (e: React.MouseEvent) => {
    // Prevent modal from closing when clicking inside the modal content
    e.stopPropagation();
  };

  const handleBackdropClick = () => {
    // Close modal when clicking the backdrop
    handleClose();
  };

  if (!isOpen) return null;

  const pricing = calculatePrice();

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      onClick={handleBackdropClick}
    >
      <div 
        className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl"
        onClick={handleModalClick}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-purple-800 text-white p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
              </div>
              <div>
                <h2 className="text-xl font-bold">Order 3D Print</h2>
                <p className="text-white/80 text-sm">{modelName}</p>
              </div>
            </div>
            <button
              onClick={handleClose}
              className="text-white/70 hover:text-white transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Progress Steps */}
          <div className="mt-6 flex items-center justify-center">
            <div className="flex items-center space-x-4">
              {[1, 2, 3].map((step) => (
                <div key={step} className="flex items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    currentStep >= step ? 'bg-white text-purple-600' : 'bg-white/20 text-white/60'
                  }`}>
                    {orderComplete && step === 3 ? (
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    ) : (
                      step
                    )}
                  </div>
                  {step < 3 && (
                    <div className={`w-16 h-1 mx-2 ${
                      currentStep > step ? 'bg-white' : 'bg-white/20'
                    }`} />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="flex max-h-[calc(90vh-140px)]">
          {/* Left Panel - Order Summary */}
          <div className="w-1/3 bg-gray-50 p-6 border-r overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Order Summary</h3>
            
            {/* Model Preview */}
            <div className="bg-white rounded-lg p-4 mb-4 shadow-sm">
              <img
                src={modelImage}
                alt={modelName}
                className="w-full h-32 object-cover rounded-lg mb-3"
              />
              <h4 className="font-medium text-gray-900 text-sm">{modelName}</h4>
              <p className="text-gray-600 text-xs">3D Model for Printing</p>
            </div>

            {/* Print Options Summary */}
            <div className="space-y-3 mb-6">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Material:</span>
                <span className="font-medium">{printOptions.material}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Color:</span>
                <span className="font-medium">{printOptions.color}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Quality:</span>
                <span className="font-medium">{printOptions.quality}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Quantity:</span>
                <span className="font-medium">{printOptions.quantity}</span>
              </div>
            </div>

            {/* Pricing Breakdown */}
            <div className="border-t pt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Subtotal:</span>
                <span>${pricing.subtotal}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Shipping:</span>
                <span>${pricing.shipping}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Tax:</span>
                <span>${pricing.tax}</span>
              </div>
              <div className="flex justify-between text-lg font-bold text-purple-600 border-t pt-2">
                <span>Total:</span>
                <span>${pricing.total}</span>
              </div>
            </div>
          </div>

          {/* Right Panel - Form Steps */}
          <div className="flex-1 p-6 overflow-y-auto">
            {/* Step 1: Print Options */}
            {currentStep === 1 && (
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-6">Print Options</h3>
                
                <div className="space-y-6">
                  {/* Material Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">Material</label>
                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { name: 'PLA', price: '$0', desc: 'Easy to print, biodegradable' },
                        { name: 'ABS', price: '+$5', desc: 'Strong, heat resistant' },
                        { name: 'PETG', price: '+$8', desc: 'Chemical resistant, clear' },
                        { name: 'TPU', price: '+$12', desc: 'Flexible, rubber-like' }
                      ].map((material) => (
                        <label key={material.name} className="relative cursor-pointer">
                          <input
                            type="radio"
                            name="material"
                            value={material.name}
                            checked={printOptions.material === material.name}
                            onChange={(e) => setPrintOptions(prev => ({ ...prev, material: e.target.value }))}
                            className="sr-only"
                          />
                          <div className={`p-4 rounded-lg border-2 transition-all ${
                            printOptions.material === material.name
                              ? 'border-purple-500 bg-purple-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}>
                            <div className="flex justify-between items-start">
                              <span className="font-medium">{material.name}</span>
                              <span className="text-sm text-purple-600">{material.price}</span>
                            </div>
                            <p className="text-xs text-gray-500 mt-1">{material.desc}</p>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Color Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">Color</label>
                    <div className="flex flex-wrap gap-2">
                      {['White', 'Black', 'Red', 'Blue', 'Green', 'Yellow'].map((color) => (
                        <button
                          key={color}
                          type="button"
                          onClick={() => setPrintOptions(prev => ({ ...prev, color }))}
                          className={`px-4 py-2 rounded-lg border text-sm ${
                            printOptions.color === color
                              ? 'border-purple-500 bg-purple-50 text-purple-700'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          {color}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Quality Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">Print Quality</label>
                    <div className="space-y-2">
                      {[
                        { name: 'Draft', price: '-$10', desc: '0.3mm layer height - Fast' },
                        { name: 'Standard', price: '$0', desc: '0.2mm layer height - Balanced' },
                        { name: 'High', price: '+$15', desc: '0.15mm layer height - Detailed' },
                        { name: 'Ultra', price: '+$30', desc: '0.1mm layer height - Premium' }
                      ].map((quality) => (
                        <label key={quality.name} className="flex items-center cursor-pointer">
                          <input
                            type="radio"
                            name="quality"
                            value={quality.name}
                            checked={printOptions.quality === quality.name}
                            onChange={(e) => setPrintOptions(prev => ({ ...prev, quality: e.target.value }))}
                            className="w-4 h-4 text-purple-600 border-gray-300 focus:ring-purple-500"
                          />
                          <div className="ml-3 flex-1">
                            <div className="flex justify-between">
                              <span className="font-medium">{quality.name}</span>
                              <span className="text-purple-600">{quality.price}</span>
                            </div>
                            <p className="text-sm text-gray-500">{quality.desc}</p>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Quantity */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Quantity</label>
                    <input
                      type="number"
                      min="1"
                      max="10"
                      value={printOptions.quantity}
                      onChange={(e) => setPrintOptions(prev => ({ ...prev, quantity: parseInt(e.target.value) || 1 }))}
                      className="w-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                </div>

                <div className="flex justify-end mt-8">
                  <button
                    onClick={handleNextStep}
                    className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
                  >
                    Continue to Shipping
                  </button>
                </div>
              </div>
            )}

            {/* Step 2: Shipping Address */}
            {currentStep === 2 && (
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-6">Shipping Address</h3>
                
                <form className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                      <input
                        type="text"
                        value={shippingAddress.fullName}
                        onChange={(e) => setShippingAddress(prev => ({ ...prev, fullName: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="John Doe"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                      <input
                        type="email"
                        value={shippingAddress.email}
                        onChange={(e) => setShippingAddress(prev => ({ ...prev, email: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="john@example.com"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Street Address</label>
                    <input
                      type="text"
                      value={shippingAddress.address}
                      onChange={(e) => setShippingAddress(prev => ({ ...prev, address: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder="123 Main Street"
                    />
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
                      <input
                        type="text"
                        value={shippingAddress.city}
                        onChange={(e) => setShippingAddress(prev => ({ ...prev, city: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="New York"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
                      <input
                        type="text"
                        value={shippingAddress.state}
                        onChange={(e) => setShippingAddress(prev => ({ ...prev, state: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="NY"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">ZIP Code</label>
                      <input
                        type="text"
                        value={shippingAddress.zipCode}
                        onChange={(e) => setShippingAddress(prev => ({ ...prev, zipCode: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="10001"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Country</label>
                    <select
                      value={shippingAddress.country}
                      onChange={(e) => setShippingAddress(prev => ({ ...prev, country: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      <option value="United States">United States</option>
                      <option value="Canada">Canada</option>
                      <option value="United Kingdom">United Kingdom</option>
                      <option value="Germany">Germany</option>
                      <option value="France">France</option>
                    </select>
                  </div>
                </form>

                <div className="flex justify-between mt-8">
                  <button
                    onClick={handlePrevStep}
                    className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                  >
                    Back
                  </button>
                  <button
                    onClick={handleNextStep}
                    className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
                  >
                    Continue to Payment
                  </button>
                </div>
              </div>
            )}

            {/* Step 3: Payment */}
            {currentStep === 3 && !orderComplete && (
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-6">Payment Information</h3>
                
                {orderProcessing ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto mb-4"></div>
                    <h4 className="text-lg font-medium text-gray-900 mb-2">Processing Payment...</h4>
                    <p className="text-gray-600">Please wait while we process your order.</p>
                  </div>
                ) : (
                  <>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                      <div className="flex items-start">
                        <svg className="w-5 h-5 text-blue-400 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                        </svg>
                        <div>
                          <h4 className="text-sm font-medium text-blue-800">Demo Payment System</h4>
                          <p className="text-sm text-blue-700 mt-1">This is a demonstration. Use any test card number like 4242 4242 4242 4242</p>
                        </div>
                      </div>
                    </div>

                    <form className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Card Number</label>
                        <input
                          type="text"
                          value={paymentInfo.cardNumber}
                          onChange={(e) => setPaymentInfo(prev => ({ ...prev, cardNumber: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          placeholder="4242 4242 4242 4242"
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Expiry Date</label>
                          <input
                            type="text"
                            value={paymentInfo.expiryDate}
                            onChange={(e) => setPaymentInfo(prev => ({ ...prev, expiryDate: e.target.value }))}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="MM/YY"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">CVV</label>
                          <input
                            type="text"
                            value={paymentInfo.cvv}
                            onChange={(e) => setPaymentInfo(prev => ({ ...prev, cvv: e.target.value }))}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="123"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Name on Card</label>
                        <input
                          type="text"
                          value={paymentInfo.nameOnCard}
                          onChange={(e) => setPaymentInfo(prev => ({ ...prev, nameOnCard: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          placeholder="John Doe"
                        />
                      </div>
                    </form>

                    <div className="flex justify-between mt-8">
                      <button
                        onClick={handlePrevStep}
                        className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                      >
                        Back
                      </button>
                      <button
                        onClick={handleSubmitOrder}
                        className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center"
                      >
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                        Place Order - ${pricing.total}
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* Order Complete */}
            {orderComplete && (
              <div className="text-center py-12">
                <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <svg className="w-10 h-10 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-4">Order Placed Successfully!</h3>
                <p className="text-gray-600 mb-2">Your order has been received and is being processed.</p>
                <p className="text-sm text-gray-500 mb-8">Order #VP-{Date.now().toString().slice(-6)}</p>
                
                <div className="bg-gray-50 rounded-lg p-6 mb-8">
                  <h4 className="font-medium text-gray-900 mb-4">What happens next?</h4>
                  <div className="space-y-3 text-sm text-gray-600">
                    <div className="flex items-start">
                      <div className="w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center mr-3 mt-0.5">
                        <span className="text-purple-600 font-bold text-xs">1</span>
                      </div>
                      <p>We'll prepare your 3D model for printing and verify the specifications.</p>
                    </div>
                    <div className="flex items-start">
                      <div className="w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center mr-3 mt-0.5">
                        <span className="text-purple-600 font-bold text-xs">2</span>
                      </div>
                      <p>Your model will be printed using {printOptions.material} material in {printOptions.color}.</p>
                    </div>
                    <div className="flex items-start">
                      <div className="w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center mr-3 mt-0.5">
                        <span className="text-purple-600 font-bold text-xs">3</span>
                      </div>
                      <p>We'll ship your printed model to {shippingAddress.city}, {shippingAddress.state}.</p>
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleClose}
                  className="px-8 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
                >
                  Continue Browsing
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
