import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';

interface ThreeViewerProps {
  modelUrl: string; // Direct GLB URL from model_3d_url
  isOpen: boolean;
  onClose: () => void;
  modelName: string;
  embedded?: boolean; // If true, render as embedded component instead of modal
}

export const ThreeViewer: React.FC<ThreeViewerProps> = ({ 
  modelUrl, 
  isOpen, 
  onClose, 
  modelName, 
  embedded = false 
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const animationIdRef = useRef<number | null>(null);
  const modelRef = useRef<THREE.Object3D | null>(null);

  const [loading, setLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Check if model URL is valid and ready
  const isModelReady = modelUrl && modelUrl.trim() !== '' && modelUrl !== 'null' && modelUrl !== 'undefined';

  // Initialize Three.js scene
  const initScene = () => {
    if (!mountRef.current) return;

    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f0f0); // Light gray background
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.set(0, 0, 5);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    rendererRef.current = renderer;

    mountRef.current.appendChild(renderer.domElement);

    // Lighting - Improved setup for better model visibility
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8); // Increased intensity and changed to white
    scene.add(ambientLight);

    // Main directional light from front-top-right
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0);
    directionalLight.position.set(5, 5, 5);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    scene.add(directionalLight);

    // Secondary directional light from front-top-left
    const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight2.position.set(-5, 5, 5);
    scene.add(directionalLight2);

    // Fill light from bottom
    const fillLight = new THREE.DirectionalLight(0xffffff, 0.4);
    fillLight.position.set(0, -5, 0);
    scene.add(fillLight);

    // Back light for better definition
    const backLight = new THREE.DirectionalLight(0xffffff, 0.6);
    backLight.position.set(0, 0, -5);
    scene.add(backLight);

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.25;
    controls.enableZoom = true;
    controlsRef.current = controls;

    // Animation loop
    const animate = () => {
      animationIdRef.current = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    console.log('🎬 Scene initialized, checking if model should load');
    // Load model if URL is already available and valid
    if (isModelReady) {
      console.log('🎯 Model URL available, triggering load');
      loadModel();
    }
  };

  // Load GLB model
  const loadModel = useCallback(async () => {
    if (!isModelReady || !sceneRef.current) {
      return;
    }

    setLoading(true);
    setLoadingProgress(0);
    setError(null);

    try {
      console.log('🎯 Loading GLB model:', modelUrl);
      
      const loader = new GLTFLoader();
      
      const gltf = await new Promise<any>((resolve, reject) => {
        loader.load(
          modelUrl,
          (loadedGltf) => {
            setLoadingProgress(100);
            resolve(loadedGltf);
          },
          (progress) => {
            if (progress.total > 0) {
              const progressPercent = Math.round((progress.loaded / progress.total) * 100);
              setLoadingProgress(progressPercent);
              console.log('📈 Loading progress:', progressPercent + '%');
            }
          },
          (error) => {
            console.error('❌ GLB loading failed:', error);
            reject(error);
          }
        );
      });

      const model = gltf.scene;
      
      // Configure model for better visibility
      model.traverse((child: any) => {
        if (child.isMesh) {
          child.castShadow = true;
          child.receiveShadow = true;
          
          // Ensure materials are properly lit
          if (child.material) {
            // Enable lighting on materials
            if (child.material.emissive) {
              child.material.emissive.setHex(0x000000);
            }
            
            // Ensure materials respond to lighting
            if (child.material.color) {
              // Don't override existing colors, just ensure they're visible
              child.material.needsUpdate = true;
            }
            
            // Set proper material properties for better visibility
            if (child.material.roughness !== undefined) {
              child.material.roughness = Math.max(0.1, child.material.roughness || 0.5);
            }
            if (child.material.metalness !== undefined) {
              child.material.metalness = Math.min(0.9, child.material.metalness || 0.0);
            }
          }
        }
      });

      // Center and scale the model
      const box = new THREE.Box3().setFromObject(model);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z);
      const scale = 3 / maxDim; // Scale to fit in viewport

      model.position.sub(center);
      model.scale.multiplyScalar(scale);

      // Remove previous model if exists
      if (modelRef.current) {
        sceneRef.current.remove(modelRef.current);
      }

      // Add new model
      sceneRef.current.add(model);
      modelRef.current = model;

      console.log('✅ 3D model loaded successfully');

    } catch (err) {
      console.error('❌ Error loading model:', err);
      setError(`Failed to load model: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  }, [modelUrl, isModelReady]);

  // Handle window resize
  const handleResize = () => {
    if (!mountRef.current || !cameraRef.current || !rendererRef.current) return;

    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight;

    cameraRef.current.aspect = width / height;
    cameraRef.current.updateProjectionMatrix();
    rendererRef.current.setSize(width, height);
  };

  // Cleanup function
  const cleanup = () => {
    if (animationIdRef.current) {
      cancelAnimationFrame(animationIdRef.current);
      animationIdRef.current = null;
    }

    if (controlsRef.current) {
      controlsRef.current.dispose();
      controlsRef.current = null;
    }

    if (rendererRef.current && mountRef.current) {
      if (rendererRef.current.domElement.parentNode === mountRef.current) {
        mountRef.current.removeChild(rendererRef.current.domElement);
      }
      rendererRef.current.dispose();
      rendererRef.current = null;
    }

    sceneRef.current = null;
    cameraRef.current = null;
    modelRef.current = null;
  };

  // Initialize scene when component opens
  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => {
        initScene();
        window.addEventListener('resize', handleResize);
      }, 100);

      return () => {
        clearTimeout(timer);
        window.removeEventListener('resize', handleResize);
        cleanup();
      };
    } else {
      cleanup();
    }
  }, [isOpen]);

  // Load model when URL changes and scene is ready
  useEffect(() => {
    console.log('🔄 ThreeViewer useEffect - checking conditions:', { 
      isOpen, 
      modelUrl: modelUrl ? modelUrl.substring(0, 50) + '...' : null, 
      hasScene: !!sceneRef.current,
      isModelReady
    });
    
    if (isOpen && isModelReady && sceneRef.current) {
      console.log('✅ All conditions met, loading model');
      loadModel();
    } else {
      console.log('❌ Conditions not met for loading');
      if (!isOpen) console.log('  - isOpen is false');
      if (!isModelReady) console.log('  - model URL not ready');
      if (!sceneRef.current) console.log('  - scene not initialized');
    }
  }, [modelUrl, isOpen, loadModel, isModelReady]);

  if (!isOpen) return null;

  // Render as embedded component
  if (embedded) {
    return (
      <div className="w-full h-full flex flex-col bg-gray-900 rounded-lg overflow-hidden">
        <div className="flex-1 relative">
          <div 
            ref={mountRef} 
            className="w-full h-full"
            style={{ minHeight: '400px' }}
          />
          
          {/* Model Not Ready State */}
          {!isModelReady && (
            <div className="absolute inset-0 bg-black bg-opacity-75 flex items-center justify-center">
              <div className="text-center max-w-sm w-full px-6">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
                <p className="text-white mb-2 text-lg font-medium">3D Model in Progress</p>
                <p className="text-white/70 text-sm mb-4">The 3D model is currently being generated. Please wait...</p>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div className="bg-gradient-to-r from-purple-600 to-purple-400 h-2 rounded-full animate-pulse"></div>
                </div>
              </div>
            </div>
          )}
          
          {/* Loading State */}
          {loading && isModelReady && (
            <div className="absolute inset-0 bg-black bg-opacity-75 flex items-center justify-center">
              <div className="text-center max-w-sm w-full px-6">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
                <p className="text-white mb-4">Loading 3D model...</p>
                
                {/* Progress Bar */}
                <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
                  <div 
                    className="bg-gradient-to-r from-purple-600 to-purple-400 h-2 rounded-full transition-all duration-300 ease-out"
                    style={{ width: `${loadingProgress}%` }}
                  ></div>
                </div>
                <p className="text-white/70 text-sm">{loadingProgress}%</p>
              </div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="absolute inset-0 bg-black bg-opacity-75 flex items-center justify-center">
              <div className="text-center text-red-400">
                <p className="mb-2">⚠️ Error loading model</p>
                <p className="text-sm text-gray-300 mb-4">{error}</p>
                <button 
                  onClick={loadModel}
                  className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
                >
                  Retry
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Render as modal
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg max-w-6xl w-full max-h-[90vh] m-4 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div>
            <h2 className="text-xl font-bold text-gray-800">{modelName}</h2>
            <p className="text-sm text-gray-600">GLB 3D Model Viewer</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
          >
            ×
          </button>
        </div>

        {/* 3D Viewer */}
        <div className="flex-1 relative bg-gray-900">
          <div 
            ref={mountRef} 
            className="w-full h-full"
            style={{ minHeight: '500px' }}
          />
          
          {/* Model Not Ready State */}
          {!isModelReady && (
            <div className="absolute inset-0 bg-black bg-opacity-75 flex items-center justify-center">
              <div className="text-center max-w-sm w-full px-6">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-white mb-2 text-lg font-medium">3D Model in Progress</p>
                <p className="text-white/70 text-sm mb-4">The 3D model is currently being generated. Please wait...</p>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div className="bg-gradient-to-r from-blue-600 to-blue-400 h-2 rounded-full animate-pulse"></div>
                </div>
              </div>
            </div>
          )}
          
          {/* Loading State */}
          {loading && isModelReady && (
            <div className="absolute inset-0 bg-black bg-opacity-75 flex items-center justify-center">
              <div className="text-center max-w-sm w-full px-6">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-white mb-4">Loading 3D model...</p>
                
                {/* Progress Bar */}
                <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
                  <div 
                    className="bg-gradient-to-r from-blue-600 to-blue-400 h-2 rounded-full transition-all duration-300 ease-out"
                    style={{ width: `${loadingProgress}%` }}
                  ></div>
                </div>
                <p className="text-white/70 text-sm">{loadingProgress}%</p>
              </div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="absolute inset-0 bg-black bg-opacity-75 flex items-center justify-center">
              <div className="text-center text-red-400">
                <p className="mb-2">⚠️ Error loading model</p>
                <p className="text-sm text-gray-300 mb-4">{error}</p>
                <button 
                  onClick={loadModel}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Retry
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-gray-50 text-sm text-gray-600">
          <p>🎮 Use mouse to rotate, scroll to zoom, right-click and drag to pan</p>
          <p>📁 Model: {isModelReady ? modelUrl : 'Generating...'}</p>
        </div>
      </div>
    </div>
  );
};