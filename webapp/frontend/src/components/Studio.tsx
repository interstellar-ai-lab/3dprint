import React, { useEffect, useRef, useState } from 'react';
import { ImageCard } from './ImageCard';

declare global {
  interface Window {
    THREE: any;
  }
}

interface GeneratedImage {
  session_id: string;
  target_object: string;
  mode: string;
  status: string;
  iterations: Array<{
    iteration: number;
    local_image_path: string;
    gcs_image_path?: string;
    gcs_url?: string;
    public_url?: string;
    evaluation?: any;
    metadata_file?: string;
  }>;
  timestamp: string;
  max_iterations: number;
  current_iteration: number;
  final_score: number;
}

export const Studio: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [scene, setScene] = useState<any>(null);
  const [camera, setCamera] = useState<any>(null);
  const [renderer, setRenderer] = useState<any>(null);
  const [controls, setControls] = useState<any>(null);
  const [objects, setObjects] = useState<any[]>([]);
  const [zipUrlInput, setZipUrlInput] = useState<string>(
    'https://storage.googleapis.com/vicino.ai/generated_3d_zip/232fb4f3-12f6-40a1-9de7-b576aa50fe9f_0.zip'
  );
  const [importedModel, setImportedModel] = useState<null | {
    model_id: string;
    serve_base_url: string;
    files: { obj?: string | null; mtl?: string | null; gltf?: string | null; glb?: string | null };
  }>(null);
  const [importStatus, setImportStatus] = useState<string>('');
  const [is3DLoading, setIs3DLoading] = useState<boolean>(false);
  const [loadingMessage, setLoadingMessage] = useState<string>('');
  const [gcsSessions, setGcsSessions] = useState<string[]>([]);
  const [selectedSession, setSelectedSession] = useState<string>('');
  const [sessionImages, setSessionImages] = useState<Array<{ 
    public_url: string; 
    gcs_image_path: string; 
    zipurl?: string; 
    has_3d?: boolean; 
    size?: number; 
    updated?: string 
  }>>([]);
  
  // Generated images state
  const [generatedImages, setGeneratedImages] = useState<GeneratedImage[]>([]);
  const [loadingImages, setLoadingImages] = useState(true);

  // Load generated images from studio backend
  const loadGeneratedImages = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/sessions');
      const data = await response.json();
      
      if (data.sessions) {
        setGeneratedImages(data.sessions);
      }
    } catch (error) {
      console.error('Error loading generated images:', error);
    } finally {
      setLoadingImages(false);
    }
  };

  useEffect(() => {
    // Load generated images
    loadGeneratedImages();
    // Load GCS sessions for public images display
    fetch('http://localhost:8001/api/studio/gcs-sessions')
      .then(r => r.json())
      .then(data => {
        if (data.sessions) {
          setGcsSessions(data.sessions);
          if (data.sessions.length > 0) {
            setSelectedSession(data.sessions[0]);
          }
        }
      })
      .catch(err => console.error('Failed to load GCS sessions', err));
    
    // Load Three.js from CDN
    const loadThreeJS = async () => {
      if (window.THREE) {
        setIsLoaded(true);
        return;
      }

      const script1 = document.createElement('script');
      script1.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
      script1.onload = () => {
        const script2 = document.createElement('script');
        script2.src = 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js';
        script2.onload = () => {
          const script3 = document.createElement('script');
          script3.src = 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/OBJLoader.js';
          script3.onload = () => {
            const script4 = document.createElement('script');
            script4.src = 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/MTLLoader.js';
            script4.onload = () => {
              const script5 = document.createElement('script');
              script5.src = 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js';
              script5.onload = () => {
                setIsLoaded(true);
              };
              document.head.appendChild(script5);
            };
            document.head.appendChild(script4);
          };
          document.head.appendChild(script3);
        };
        document.head.appendChild(script2);
      };
      document.head.appendChild(script1);
    };

    loadThreeJS();
  }, []);

  useEffect(() => {
    if (!isLoaded || !containerRef.current) return;

    const THREE = window.THREE;
    if (!THREE) return;

    // Scene setup
    const newScene = new THREE.Scene();
    newScene.background = new THREE.Color(0x1a1a1a);

    // Camera setup
    const container = containerRef.current;
    const aspect = container.clientWidth / container.clientHeight;
    const newCamera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
    newCamera.position.set(5, 5, 5);

    // Renderer setup
    const newRenderer = new THREE.WebGLRenderer({ antialias: true });
    newRenderer.setSize(container.clientWidth, container.clientHeight);
    newRenderer.shadowMap.enabled = true;
    newRenderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(newRenderer.domElement);

    // Controls setup
    const newControls = new THREE.OrbitControls(newCamera, newRenderer.domElement);
    newControls.enableDamping = true;
    newControls.dampingFactor = 0.05;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
    newScene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(10, 10, 5);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    newScene.add(directionalLight);

    // Grid Helper
    const gridHelper = new THREE.GridHelper(20, 20, 0x444444, 0x222222);
    newScene.add(gridHelper);

    // Axes Helper
    const axesHelper = new THREE.AxesHelper(5);
    newScene.add(axesHelper);

    // Load 3D model
    load3DModel(newScene, newCamera, newControls);

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);

      // Rotate objects
      objects.forEach((obj: any, index: number) => {
        obj.rotation.x += 0.01 * (index + 1);
        obj.rotation.y += 0.01 * (index + 1);
      });

      newControls.update();
      newRenderer.render(newScene, newCamera);
    };

    animate();

    // Handle window resize
    const handleResize = () => {
      const container = containerRef.current;
      if (!container) return;

      newCamera.aspect = container.clientWidth / container.clientHeight;
      newCamera.updateProjectionMatrix();
      newRenderer.setSize(container.clientWidth, container.clientHeight);
    };

    window.addEventListener('resize', handleResize);

    // Set state
    setScene(newScene);
    setCamera(newCamera);
    setRenderer(newRenderer);
    setControls(newControls);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (containerRef.current && newRenderer.domElement) {
        containerRef.current.removeChild(newRenderer.domElement);
      }
      newRenderer.dispose();
    };
  }, [isLoaded]);

  const load3DModel = (targetScene: any, targetCamera: any, targetControls: any) => {
    if (!window.THREE) return;

    const THREE = window.THREE;
    const mtlLoader = new THREE.MTLLoader();
    const objLoader = new THREE.OBJLoader();
    
    // Load material first
    mtlLoader.load(
      '/models/material.mtl',
      function(materials: any) {
        materials.preload();
        
        // Load OBJ with materials
        objLoader.setMaterials(materials);
        objLoader.load(
          '/models/3c79ca5cdb13fb2b0e9a62da0c058ff5.obj',
          function(object: any) {
            // Center and scale the model
            const box = new THREE.Box3().setFromObject(object);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            
            // Calculate scale to fit in view
            const maxDim = Math.max(size.x, size.y, size.z);
            const scale = 5 / maxDim; // Scale to fit in 5 unit cube
            
            object.position.sub(center);
            object.scale.setScalar(scale);
            
            // Enable shadows for all meshes
            object.traverse(function(child: any) {
              if (child.isMesh) {
                child.castShadow = true;
                child.receiveShadow = true;
              }
            });
            
            targetScene.add(object);
            
            // Adjust camera to view the model
            const distance = maxDim * 2;
            targetCamera.position.set(distance, distance, distance);
            targetCamera.lookAt(0, 0, 0);
            targetControls.target.set(0, 0, 0);
            targetControls.update();
            
            console.log('3D Model loaded successfully');
          },
          function(xhr: any) {
            const percent = (xhr.loaded / xhr.total * 100).toFixed(0);
            console.log(`Loading 3D model: ${percent}%`);
          },
          function(error: any) {
            console.error('Error loading OBJ file:', error);
          }
        );
      },
      function(xhr: any) {
        console.log('Loading materials...', (xhr.loaded / xhr.total * 100) + '%');
      },
      function(error: any) {
        console.error('Error loading materials:', error);
      }
    );
  };

  const centerAndScaleObject = (targetScene: any, targetCamera: any, targetControls: any, object: any) => {
    const THREE = window.THREE;
    const box = new THREE.Box3().setFromObject(object);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z) || 1;
    const scale = 5 / maxDim;
    object.position.sub(center);
    object.scale.setScalar(scale);
    object.traverse(function(child: any) {
      if (child.isMesh) {
        child.castShadow = true;
        child.receiveShadow = true;
      }
    });
    targetScene.add(object);
    const distance = maxDim * 2;
    targetCamera.position.set(distance, distance, distance);
    targetCamera.lookAt(0, 0, 0);
    targetControls.target.set(0, 0, 0);
    targetControls.update();
  };

  const importModelFromZip = async () => {
    try {
      setIs3DLoading(true);
      setLoadingMessage('Downloading ZIP...');
      setImportStatus('Importing...');
      
      const response = await fetch('http://localhost:8001/api/studio/import-model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zip_url: zipUrlInput }),
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || `HTTP ${response.status}`);
      }
      const data = await response.json();
      setImportedModel(data);
      setImportStatus('Imported. Loading model...');
      setLoadingMessage('Loading 3D model...');
      
      // Auto-load immediately after successful import
      if (scene && camera && controls) {
        // Optional: clear existing objects before loading new model
        clearScene();
        loadImportedModel(scene, camera, controls, data);
      }
    } catch (e: any) {
      console.error('Failed to import model:', e);
      setImportStatus(`Error: ${e.message || String(e)}`);
      setIs3DLoading(false);
      setLoadingMessage('');
    }
  };

  const loadImportedModel = (
    targetScene: any,
    targetCamera: any,
    targetControls: any,
    model?: { model_id: string; serve_base_url: string; files: { obj?: string | null; mtl?: string | null; gltf?: string | null; glb?: string | null } }
  ) => {
    if (!window.THREE) return;
    const selectedModel = model || importedModel;
    if (!selectedModel) return;
    const THREE = window.THREE;
    const baseUrl = `http://localhost:8001${selectedModel.serve_base_url}`;

    // Prefer GLB, then GLTF, then OBJ+MTL
    if (selectedModel.files.glb && (THREE as any).GLTFLoader) {
      const loader = new (THREE as any).GLTFLoader();
      loader.load(
        baseUrl + selectedModel.files.glb,
        (gltf: any) => {
          const object = gltf.scene || (gltf.scenes && gltf.scenes[0]);
          if (object) {
            centerAndScaleObject(targetScene, targetCamera, targetControls, object);
            setObjects(prev => [...prev, object]);
            setImportStatus('Loaded');
            setIs3DLoading(false);
            setLoadingMessage('');
          }
        },
        (progress: any) => {
          if (progress.total > 0) {
            const percent = Math.round((progress.loaded / progress.total) * 100);
            setLoadingMessage(`Loading GLB... ${percent}%`);
          }
        },
        (error: any) => {
          console.error('GLB load error:', error);
          setImportStatus('Failed to load GLB');
          setIs3DLoading(false);
          setLoadingMessage('');
        }
      );
      return;
    }
    if (selectedModel.files.gltf && (THREE as any).GLTFLoader) {
      const loader = new (THREE as any).GLTFLoader();
      loader.load(
        baseUrl + selectedModel.files.gltf,
        (gltf: any) => {
          const object = gltf.scene || (gltf.scenes && gltf.scenes[0]);
          if (object) {
            centerAndScaleObject(targetScene, targetCamera, targetControls, object);
            setObjects(prev => [...prev, object]);
            setImportStatus('Loaded');
            setIs3DLoading(false);
            setLoadingMessage('');
          }
        },
        (progress: any) => {
          if (progress.total > 0) {
            const percent = Math.round((progress.loaded / progress.total) * 100);
            setLoadingMessage(`Loading GLTF... ${percent}%`);
          }
        },
        (error: any) => {
          console.error('GLTF load error:', error);
          setImportStatus('Failed to load GLTF');
          setIs3DLoading(false);
          setLoadingMessage('');
        }
      );
      return;
    }
    if (selectedModel.files.obj) {
      const objLoader = new (THREE as any).OBJLoader();
      const mtlPath = selectedModel.files.mtl ? baseUrl + selectedModel.files.mtl : null;
      if (mtlPath && (THREE as any).MTLLoader) {
        const mtlLoader = new (THREE as any).MTLLoader();
        // Ensure textures referenced in MTL load correctly
        const mtlDir = selectedModel.files.mtl ? (selectedModel.files.mtl as string).split('/').slice(0, -1).join('/') : '';
        if (mtlDir) {
          (mtlLoader as any).setResourcePath(baseUrl + mtlDir + '/');
        }
        mtlLoader.load(mtlPath, (materials: any) => {
          materials.preload();
          objLoader.setMaterials(materials);
          // Ensure any relative references inside OBJ load correctly
          const objDir = (selectedModel.files.obj as string).split('/').slice(0, -1).join('/');
          if (objDir) {
            (objLoader as any).setPath(baseUrl + objDir + '/');
          }
          objLoader.load(
            baseUrl + selectedModel.files.obj,
            (object: any) => {
              centerAndScaleObject(targetScene, targetCamera, targetControls, object);
              setObjects(prev => [...prev, object]);
              setImportStatus('Loaded');
              setIs3DLoading(false);
              setLoadingMessage('');
            },
            (progress: any) => {
              if (progress.total > 0) {
                const percent = Math.round((progress.loaded / progress.total) * 100);
                setLoadingMessage(`Loading OBJ... ${percent}%`);
              }
            },
            (error: any) => {
              console.error('OBJ load error:', error);
              setImportStatus('Failed to load OBJ');
              setIs3DLoading(false);
              setLoadingMessage('');
            }
          );
        });
      } else {
        const objDir = (selectedModel.files.obj as string).split('/').slice(0, -1).join('/');
        if (objDir) {
          (objLoader as any).setPath(baseUrl + objDir + '/');
        }
        objLoader.load(
          baseUrl + selectedModel.files.obj,
          (object: any) => {
            centerAndScaleObject(targetScene, targetCamera, targetControls, object);
            setObjects(prev => [...prev, object]);
            setImportStatus('Loaded');
            setIs3DLoading(false);
            setLoadingMessage('');
          },
          (progress: any) => {
            if (progress.total > 0) {
              const percent = Math.round((progress.loaded / progress.total) * 100);
              setLoadingMessage(`Loading OBJ... ${percent}%`);
            }
          },
          (error: any) => {
            console.error('OBJ load error:', error);
            setImportStatus('Failed to load OBJ');
            setIs3DLoading(false);
            setLoadingMessage('');
          }
        );
      }
    }
  };

  const handleView3D = async (zipurl: string) => {
    try {
      setIs3DLoading(true);
      setLoadingMessage('Downloading 3D model...');
      setZipUrlInput(zipurl);
      
      const response = await fetch('http://localhost:8001/api/studio/import-model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zip_url: zipurl }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      setImportedModel(data);
      setLoadingMessage('Loading 3D model...');
      
      if (scene && camera && controls) {
        clearScene();
        loadImportedModel(scene, camera, controls, data);
      }
    } catch (err) {
      console.error('Failed to load 3D model:', err);
      setIs3DLoading(false);
      setLoadingMessage('');
      alert('Failed to load 3D model. Please try again.');
    }
  };

  const handleGenerate3D = () => {
    // TODO: Implement 3D generation workflow
    alert('3D generation coming soon!');
  };

  const addCube = (targetScene: any, THREE: any) => {
    const geometry = new THREE.BoxGeometry(1, 1, 1);
    const material = new THREE.MeshLambertMaterial({ 
      color: Math.random() * 0xffffff,
      transparent: true,
      opacity: 0.8
    });
    const cube = new THREE.Mesh(geometry, material);
    cube.position.set(
      (Math.random() - 0.5) * 4,
      (Math.random() - 0.5) * 4,
      (Math.random() - 0.5) * 4
    );
    cube.castShadow = true;
    cube.receiveShadow = true;
    targetScene.add(cube);
    return [cube];
  };

  const addSphere = () => {
    if (!scene || !window.THREE) return;

    const THREE = window.THREE;
    const geometry = new THREE.SphereGeometry(0.5, 32, 32);
    const material = new THREE.MeshLambertMaterial({ 
      color: Math.random() * 0xffffff,
      transparent: true,
      opacity: 0.8
    });
    const sphere = new THREE.Mesh(geometry, material);
    sphere.position.set(
      (Math.random() - 0.5) * 4,
      (Math.random() - 0.5) * 4,
      (Math.random() - 0.5) * 4
    );
    sphere.castShadow = true;
    sphere.receiveShadow = true;
    scene.add(sphere);
    setObjects(prev => [...prev, sphere]);
  };

  const clearScene = () => {
    if (!scene) return;

    objects.forEach(obj => {
      scene.remove(obj);
    });
    setObjects([]);
  };

  useEffect(() => {
    if (!selectedSession) return;
    fetch(`http://localhost:8001/api/studio/gcs-session-images/${selectedSession}`)
      .then(r => r.json())
      .then(data => {
        setSessionImages(data.images || []);
      })
      .catch(err => console.error('Failed to load session images', err));
  }, [selectedSession]);

  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p>Loading 3D Studio...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 to-blue-600 pb-16">
      {/* Header */}
      <div className="bg-white/95 backdrop-blur-md shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-purple-600">Vicino 3D Studio</h1>
            <a href="/" className="text-purple-600 hover:text-purple-700 font-medium">
              ← Back to Home
            </a>
          </div>
        </div>
      </div>

      {/* 3D Viewer */}
      <div className="container mx-auto px-4 py-8">
        <div className="bg-gray-900 rounded-2xl shadow-2xl overflow-hidden relative">
          <div 
            ref={containerRef} 
            className="w-full h-96 md:h-[600px]"
          />
          
          {/* 3D Loading Overlay */}
          {is3DLoading && (
            <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-50">
              <div className="bg-white/95 backdrop-blur-md rounded-xl p-6 shadow-lg text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
                <p className="text-gray-800 font-semibold">{loadingMessage || 'Loading 3D Model...'}</p>
                <p className="text-gray-600 text-sm mt-2">Please wait while we prepare your 3D model</p>
              </div>
            </div>
          )}
          
          {/* Controls Panel */}
          <div className="absolute top-4 right-4 bg-white/95 backdrop-blur-md rounded-xl p-4 shadow-lg">
            <div className="space-y-4">
                             <div>
                 <h3 className="font-semibold text-gray-800 mb-2">3D Model</h3>
                 <div className="space-y-2">
                   <button 
                     onClick={() => {
                       if (scene && camera && controls) {
                         load3DModel(scene, camera, controls);
                       }
                     }}
                     className="w-full px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
                   >
                     Load 3D Model
                   </button>
                 </div>
               </div>
               
               <div>
                 <h3 className="font-semibold text-gray-800 mb-2">Primitives</h3>
                 <div className="space-y-2">
                   <button 
                     onClick={() => {
                       if (scene && window.THREE) {
                         const newObjects = addCube(scene, window.THREE);
                         setObjects(prev => [...prev, ...newObjects]);
                       }
                     }}
                     className="w-full px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm"
                   >
                     Add Cube
                   </button>
                   <button 
                     onClick={addSphere}
                     className="w-full px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                   >
                     Add Sphere
                   </button>
                   <button 
                     onClick={clearScene}
                     className="w-full px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
                   >
                     Clear Scene
                   </button>
                 </div>
               </div>
              
              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Info</h3>
                <div className="text-xs text-gray-600 space-y-1">
                  <p>• Left click + drag: Rotate</p>
                  <p>• Right click + drag: Pan</p>
                  <p>• Scroll: Zoom</p>
                  <p>Objects: {objects.length}</p>
                </div>
              </div>
              
              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Import 3D Model (ZIP)</h3>
                <div className="space-y-2">
                  <input
                    type="text"
                    value={zipUrlInput}
                    onChange={(e) => setZipUrlInput(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg text-sm"
                    placeholder="https://.../model.zip"
                  />
                  <button
                    onClick={importModelFromZip}
                    className="w-full px-3 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm"
                  >
                    Import ZIP
                  </button>
                  {importStatus && (
                    <p className="text-xs text-gray-600">{importStatus}</p>
                  )}
                  {importedModel && (
                    <button
                      onClick={() => {
                        if (scene && camera && controls) {
                          loadImportedModel(scene, camera, controls);
                        }
                      }}
                      className="w-full px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                    >
                      Load Imported Model
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Public GCS Generated Images Section */}
      <div className="container mx-auto px-4 py-8 pb-16">
        <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl p-6">
          <div className="mb-6">
            <h2 className="text-3xl font-bold text-gray-800 mb-2">Generated Images</h2>
            <div className="mt-4 flex gap-3 items-center">
              <label className="text-sm text-gray-700">Session:</label>
              <select
                value={selectedSession}
                onChange={(e) => setSelectedSession(e.target.value)}
                className="px-3 py-2 border rounded-lg text-sm"
              >
                {gcsSessions.map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>

          {sessionImages.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600">No images found for this session.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-8">
              {sessionImages.map((img) => (
                <ImageCard
                  key={img.gcs_image_path}
                  img={img}
                  onView3D={handleView3D}
                  onGenerate3D={handleGenerate3D}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
