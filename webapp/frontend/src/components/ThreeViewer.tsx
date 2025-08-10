import React, { useRef, useEffect, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import JSZip from 'jszip';

interface ThreeViewerProps {
  zipUrl: string;
  isOpen: boolean;
  onClose: () => void;
  modelName: string;
  imagePath?: string; // Add image path to construct proxy URL
  onMaterialDataChange?: (data: {
    materialMode: 'full' | 'texture-only' | 'basic';
    materialBlendMode: 'white-base' | 'mtl-tint' | 'auto';
    availableMaterials: {
      hasMTL: boolean;
      hasTextures: boolean;
      textureCount: number;
    };
    onMaterialModeChange: (mode: 'full' | 'texture-only' | 'basic') => void;
    onMaterialBlendModeChange: (mode: 'white-base' | 'mtl-tint' | 'auto') => void;
  }) => void;
}

export const ThreeViewer: React.FC<ThreeViewerProps> = ({ zipUrl, isOpen, onClose, modelName, imagePath, onMaterialDataChange }) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const animationIdRef = useRef<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modelData, setModelData] = useState<any>(null);
  const [materialMode, setMaterialMode] = useState<'full' | 'texture-only' | 'basic'>('full');
  const [materialBlendMode, setMaterialBlendMode] = useState<'white-base' | 'mtl-tint' | 'auto'>('white-base');
  const [availableMaterials, setAvailableMaterials] = useState<{
    hasMTL: boolean;
    hasTextures: boolean;
    textureCount: number;
  }>({ hasMTL: false, hasTextures: false, textureCount: 0 });
  
  // Store loaded assets for material switching
  const [loadedAssets, setLoadedAssets] = useState<{
    objData: string | null;
    materialData: string | null;
    textures: { [key: string]: string } | null;
  }>({ objData: null, materialData: null, textures: null });

  // Initialize Three.js scene
  const initScene = () => {
    if (!mountRef.current) return;

    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf5f5f5);
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
    rendererRef.current = renderer;

    mountRef.current.appendChild(renderer.domElement);

    // Enhanced Lighting for better texture visibility
    const ambientLight = new THREE.AmbientLight(0x404040, 0.8); // Increased ambient light
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0); // Increased intensity
    directionalLight.position.set(5, 5, 5);
    directionalLight.castShadow = true;
    scene.add(directionalLight);

    // Add additional light from the front to illuminate textures better
    const frontLight = new THREE.DirectionalLight(0xffffff, 0.6);
    frontLight.position.set(0, 0, 5);
    scene.add(frontLight);

    // Grid helper
    const gridHelper = new THREE.GridHelper(10, 10);
    gridHelper.material.opacity = 0.3;
    gridHelper.material.transparent = true;
    scene.add(gridHelper);

    // Set up OrbitControls for proper camera interaction
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true; // Smooth camera movements
    controls.dampingFactor = 0.05;
    controls.screenSpacePanning = false;
    controls.minDistance = 1;
    controls.maxDistance = 20;
    controls.maxPolarAngle = Math.PI; // Allow full rotation
    
    // Configure controls for better UX
    controls.enableZoom = true;
    controls.enableRotate = true;
    controls.enablePan = true;
    controls.autoRotate = false;
    controls.zoomSpeed = 1.0;
    controls.rotateSpeed = 1.0;
    controls.panSpeed = 0.8;
    
    controlsRef.current = controls;

    // Animation loop
    const animate = () => {
      animationIdRef.current = requestAnimationFrame(animate);
      
      // Update controls for smooth damping
      if (controlsRef.current) {
        controlsRef.current.update();
      }
      
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      // Cleanup controls
      if (controlsRef.current) {
        controlsRef.current.dispose();
      }
    };
  };

  // Load 3D model from zip
  // Reload model with current material mode
  const reloadModelWithMaterialMode = async () => {
    if (!loadedAssets.objData) return;
    
    setLoading(true);
    try {
      await loadModelData(
        'model.obj', // Filename doesn't matter for reload
        loadedAssets.objData,
        loadedAssets.materialData,
        loadedAssets.textures || undefined
      );
      console.log('Model reloaded with material mode:', materialMode);
    } catch (error) {
      console.error('Error reloading model:', error);
      setError('Failed to reload model with new material settings');
    } finally {
      setLoading(false);
    }
  };

  const loadModel = async () => {
    if (!zipUrl) return;

    setLoading(true);
    setError(null);

    try {
      console.log('Loading model from:', zipUrl);

      // Step 1: Use proxy endpoint to fetch the zip file (bypasses CORS)
      const proxyUrl = imagePath 
        ? `http://localhost:8001/api/studio/proxy-zip/${imagePath}`
        : zipUrl;
      
      console.log('Using proxy URL:', proxyUrl);
      
      const response = await fetch(proxyUrl);
      if (!response.ok) {
        throw new Error(`Failed to fetch zip file: ${response.statusText}`);
      }

      const arrayBuffer = await response.arrayBuffer();
      
      // Step 2: Unzip the file
      const zip = new JSZip();
      const zipContents = await zip.loadAsync(arrayBuffer);
      
      console.log('Zip contents:', Object.keys(zipContents.files));

      // Step 3: Find 3D model files and materials
      const modelFiles = Object.keys(zipContents.files).filter(filename => {
        const ext = filename.toLowerCase().split('.').pop();
        return ['obj', 'ply', 'stl', 'dae', 'gltf', 'glb', 'fbx'].includes(ext || '');
      });

      const materialFiles = Object.keys(zipContents.files).filter(filename => 
        filename.toLowerCase().endsWith('.mtl')
      );

      const textureFiles = Object.keys(zipContents.files).filter(filename => {
        const ext = filename.toLowerCase().split('.').pop();
        return ['png', 'jpg', 'jpeg', 'bmp', 'tga'].includes(ext || '');
      });

      console.log('Found model files:', modelFiles);
      console.log('Found material files:', materialFiles);
      console.log('Found texture files:', textureFiles);

      if (modelFiles.length === 0) {
        // No model files found, create a placeholder
        await createPlaceholderModel();
        return;
      }

      // Step 4: Load model with materials and textures
      const modelFile = modelFiles[0];
      const fileData = await zipContents.files[modelFile].async('text');
      
      // Load material file if available
      let materialData = null;
      if (materialFiles.length > 0) {
        materialData = await zipContents.files[materialFiles[0]].async('text');
        console.log('Loaded material file:', materialFiles[0]);
      }

      // Load texture files as data URLs
      const textures: { [key: string]: string } = {};
      for (const textureFile of textureFiles) {
        try {
          const textureBlob = await zipContents.files[textureFile].async('blob');
          const dataUrl = URL.createObjectURL(textureBlob);
          textures[textureFile] = dataUrl;
          console.log('✅ Loaded texture:', textureFile, 'Size:', textureBlob.size, 'bytes');
          console.log('🔗 Texture URL:', dataUrl.substring(0, 50) + '...');
        } catch (error) {
          console.warn('❌ Failed to load texture:', textureFile, error);
        }
      }
      
      // Store loaded assets for material switching
      setLoadedAssets({
        objData: fileData,
        materialData: materialData,
        textures: Object.keys(textures).length > 0 ? textures : null
      });
      
      // Set available materials info
      setAvailableMaterials({
        hasMTL: materialFiles.length > 0,
        hasTextures: textureFiles.length > 0,
        textureCount: textureFiles.length
      });
      
      await loadModelData(modelFile, fileData, materialData, textures);

    } catch (err) {
      console.error('Error loading model:', err);
      setError(`Failed to load 3D model: ${err instanceof Error ? err.message : 'Unknown error'}`);
      // Fallback to placeholder
      await createPlaceholderModel();
    } finally {
      setLoading(false);
    }
  };

  // Create a placeholder model when real model can't be loaded
  const createPlaceholderModel = async () => {
    const geometry = new THREE.BoxGeometry(2, 2, 2);
    const material = new THREE.MeshLambertMaterial({ 
      color: 0x9333ea, // Purple color
      wireframe: false 
    });
    const cube = new THREE.Mesh(geometry, material);
    cube.castShadow = true;
    cube.receiveShadow = true;

    if (sceneRef.current) {
      // Remove previous model if exists
      if (modelData) {
        sceneRef.current.remove(modelData);
      }

      sceneRef.current.add(cube);
      setModelData(cube);
      console.log('Placeholder cube model created');
    }
  };

  // Load model data based on file type with materials and textures
  const loadModelData = async (filename: string, data: string, materialData?: string | null, textures?: { [key: string]: string }) => {
    const ext = filename.toLowerCase().split('.').pop();
    
    try {
      if (ext === 'obj') {
        await loadOBJModel(data, materialData, textures);
      } else if (ext === 'ply') {
        await loadPLYModel(data);
      } else if (ext === 'stl') {
        await loadSTLModel(data);
      } else {
        console.log(`Format ${ext} not yet supported, using placeholder`);
        await createPlaceholderModel();
      }
    } catch (error) {
      console.error(`Error loading ${ext} model:`, error);
      await createPlaceholderModel();
    }
  };

  // Load OBJ model with materials and textures
  const loadOBJModel = async (objData: string, materialData?: string | null, textures?: { [key: string]: string }) => {
    try {
      // Parse OBJ geometry
      const geometry = parseOBJ(objData);
      
      // Create material based on current mode and available assets
      let material: THREE.Material;
      
      if (materialMode === 'full' && materialData && textures) {
        // Parse MTL file and create material
        material = await parseMTLAndCreateMaterial(materialData, textures);
      } else if ((materialMode === 'full' || materialMode === 'texture-only') && textures && Object.keys(textures).length > 0) {
        // Use texture without MTL file
        const firstTextureUrl = Object.values(textures)[0];
        const firstTextureName = Object.keys(textures)[0];
        
        console.log('🎨 Loading texture (no MTL):', firstTextureName, 'from URL:', firstTextureUrl);
        
        const loader = new THREE.TextureLoader();
        const texture = await new Promise<THREE.Texture>((resolve, reject) => {
          loader.load(
            firstTextureUrl,
            (loadedTexture) => {
              console.log('✅ Texture loaded successfully (no MTL)');
              resolve(loadedTexture);
            },
            (progress) => {
              console.log('📈 Texture loading progress (no MTL):', progress);
            },
            (error) => {
              console.error('❌ Texture loading failed (no MTL):', error);
              reject(error);
            }
          );
        });
        
        // Configure texture properties
        texture.wrapS = THREE.RepeatWrapping;
        texture.wrapT = THREE.RepeatWrapping;
        texture.minFilter = THREE.LinearMipmapLinearFilter;
        texture.magFilter = THREE.LinearFilter;
        texture.generateMipmaps = true;
        
        material = new THREE.MeshPhongMaterial({ 
          map: texture,
          color: 0xcccccc, // Use the same default gray as MTL would
          side: THREE.DoubleSide,
          shininess: 30
        });
        console.log('✅ Applied texture without MTL file');
      } else {
        // Basic material mode or fallback
        material = new THREE.MeshPhongMaterial({ 
          color: 0xdddddd, // Light gray
          side: THREE.DoubleSide,
          shininess: 30
        });
        console.log('Using basic material');
      }
      
      const mesh = new THREE.Mesh(geometry, material);
      mesh.castShadow = true;
      mesh.receiveShadow = true;

      // Center and scale the model
      const box = new THREE.Box3().setFromObject(mesh);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z);
      const scale = 3 / maxDim; // Scale to fit in a 3-unit cube

      mesh.position.sub(center);
      mesh.scale.multiplyScalar(scale);

      if (sceneRef.current) {
        if (modelData) {
          sceneRef.current.remove(modelData);
        }
        sceneRef.current.add(mesh);
        setModelData(mesh);
        console.log('OBJ model loaded successfully with', geometry.attributes.position.count, 'vertices');
        console.log('Material applied:', material.type);
      }
    } catch (error) {
      console.error('Error loading OBJ:', error);
      await createPlaceholderModel();
    }
  };

  // Parse MTL file and create material
  const parseMTLAndCreateMaterial = async (mtlData: string, textures: { [key: string]: string }): Promise<THREE.Material> => {
    const lines = mtlData.split('\n');
    let currentMaterial: any = {
      name: 'default',
      color: [0.8, 0.8, 0.8], // Default gray (#cccccc)
      ambient: [0.2, 0.2, 0.2], // Default ambient (#333333)
      specular: [0.5, 0.5, 0.5], // Default specular (#808080)
      shininess: 30,
      map: null
    };

    for (const line of lines) {
      const parts = line.trim().split(/\s+/);
      if (parts.length === 0) continue;

      switch (parts[0]) {
        case 'newmtl':
          currentMaterial.name = parts[1];
          break;
        case 'Ka': // Ambient color
          currentMaterial.ambient = [parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3])];
          break;
        case 'Kd': // Diffuse color
          currentMaterial.color = [parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3])];
          break;
        case 'Ks': // Specular color
          currentMaterial.specular = [parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3])];
          break;
        case 'Ns': // Shininess
          currentMaterial.shininess = parseFloat(parts[1]);
          break;
        case 'map_Kd': // Diffuse texture map
          const textureName = parts[1];
          console.log('Looking for texture:', textureName);
          
          // Find matching texture file (more flexible matching)
          const matchingTexture = Object.keys(textures).find(key => {
            const keyLower = key.toLowerCase();
            const textureNameLower = textureName.toLowerCase();
            const keyBaseName = keyLower.split('.')[0];
            const textureBaseName = textureNameLower.split('.')[0];
            
            return keyLower === textureNameLower || // Exact match
                   keyLower.includes(textureNameLower) || // Key contains texture name
                   textureNameLower.includes(keyLower) || // Texture name contains key
                   keyBaseName === textureBaseName || // Base names match
                   keyLower.includes('material') || // Generic material texture
                   keyLower.includes('diffuse') || // Diffuse texture
                   keyLower.includes('color'); // Color texture
          });
          
          if (matchingTexture) {
            currentMaterial.map = textures[matchingTexture];
            console.log('✅ Found texture mapping:', textureName, '→', matchingTexture);
          } else {
            console.log('❌ No matching texture found for:', textureName);
            console.log('Available textures:', Object.keys(textures));
          }
          break;
      }
    }

    // Create Three.js material with original MTL colors
    const diffuseColor = new THREE.Color(currentMaterial.color[0], currentMaterial.color[1], currentMaterial.color[2]);
    const specularColor = new THREE.Color(currentMaterial.specular[0], currentMaterial.specular[1], currentMaterial.specular[2]);
    
    console.log('🎨 Creating material with MTL properties:');
    console.log('  - Diffuse (Kd):', diffuseColor.getHexString());
    console.log('  - Ambient (Ka):', currentMaterial.ambient);
    console.log('  - Specular (Ks):', specularColor.getHexString());
    console.log('  - Shininess (Ns):', currentMaterial.shininess);
    
    // Apply different blending strategies based on materialBlendMode
    let materialColor;
    switch (materialBlendMode) {
      case 'white-base':
        materialColor = currentMaterial.map ? 0xffffff : diffuseColor;
        break;
      case 'mtl-tint':
        materialColor = diffuseColor; // Use MTL color even with texture (for tinting effect)
        break;
      case 'auto':
      default:
        // Use a lighter version of MTL color to preserve some tinting but not darken too much
        const lightness = (diffuseColor.r + diffuseColor.g + diffuseColor.b) / 3;
        materialColor = currentMaterial.map && lightness < 0.8 ? 
          new THREE.Color().lerpColors(diffuseColor, new THREE.Color(1, 1, 1), 0.5) : 
          diffuseColor;
        break;
    }
    
    console.log('🎨 Material color strategy:', materialBlendMode);
    console.log('  - Has texture map:', !!currentMaterial.map);
    console.log('  - MTL diffuse color:', diffuseColor.getHexString());
    console.log('  - Final material color:', typeof materialColor === 'number' ? materialColor.toString(16) : materialColor.getHexString());
    
    const material = new THREE.MeshPhongMaterial({
      color: materialColor,
      specular: specularColor,
      shininess: currentMaterial.shininess,
      side: THREE.DoubleSide
    });

    // Apply texture if available
    if (currentMaterial.map) {
      console.log('🎨 Loading texture from URL:', currentMaterial.map);
      const loader = new THREE.TextureLoader();
      
      // Create a promise to properly handle texture loading
      const texture = await new Promise<THREE.Texture>((resolve, reject) => {
        loader.load(
          currentMaterial.map,
          (loadedTexture) => {
            console.log('✅ Texture loaded successfully');
            resolve(loadedTexture);
          },
          (progress) => {
            console.log('📈 Texture loading progress:', progress);
          },
          (error) => {
            console.error('❌ Texture loading failed:', error);
            reject(error);
          }
        );
      });
      
      // Configure texture properties
      texture.wrapS = THREE.RepeatWrapping;
      texture.wrapT = THREE.RepeatWrapping;
      texture.minFilter = THREE.LinearMipmapLinearFilter;
      texture.magFilter = THREE.LinearFilter;
      texture.generateMipmaps = true;
      
      material.map = texture;
      console.log('✅ Applied texture from MTL file to material');
      
      // Debug material properties
      console.log('🔍 Material properties:');
      console.log('  - Color:', material.color.getHexString());
      console.log('  - Has texture map:', !!material.map);
      console.log('  - Texture size:', material.map ? `${material.map.image?.width}x${material.map.image?.height}` : 'N/A');
    }

    console.log('Created material from MTL:', currentMaterial.name);
    return material;
  };

  // Enhanced OBJ parser with UV coordinates
  const parseOBJ = (objData: string): THREE.BufferGeometry => {
    const vertices: number[] = [];
    const uvs: number[] = [];
    const faces: number[] = [];
    const faceUVs: number[] = [];
    const lines = objData.split('\n');

    console.log('Parsing OBJ with', lines.length, 'lines');

    for (const line of lines) {
      const parts = line.trim().split(/\s+/);
      
      if (parts[0] === 'v' && parts.length >= 4) {
        // Vertex position
        vertices.push(
          parseFloat(parts[1]) || 0,
          parseFloat(parts[2]) || 0,
          parseFloat(parts[3]) || 0
        );
      } else if (parts[0] === 'vt' && parts.length >= 3) {
        // UV texture coordinates
        uvs.push(
          parseFloat(parts[1]) || 0,
          1.0 - (parseFloat(parts[2]) || 0) // Flip V coordinate for Three.js
        );
      } else if (parts[0] === 'f' && parts.length >= 4) {
        // Face - convert to triangles if needed
        const faceVertices = [];
        const faceUVIndices = [];
        
        for (let i = 1; i < parts.length; i++) {
          const indices = parts[i].split('/');
          const vertexIndex = parseInt(indices[0]) - 1; // OBJ is 1-indexed
          const uvIndex = indices.length > 1 && indices[1] ? parseInt(indices[1]) - 1 : -1;
          
          faceVertices.push(vertexIndex);
          faceUVIndices.push(uvIndex);
        }
        
        // Triangulate the face (for quads and polygons)
        for (let i = 1; i < faceVertices.length - 1; i++) {
          const v1 = faceVertices[0];
          const v2 = faceVertices[i];
          const v3 = faceVertices[i + 1];
          
          const uv1 = faceUVIndices[0];
          const uv2 = faceUVIndices[i];
          const uv3 = faceUVIndices[i + 1];
          
          // Validate indices before adding
          if (v1 >= 0 && v1 < vertices.length / 3 &&
              v2 >= 0 && v2 < vertices.length / 3 &&
              v3 >= 0 && v3 < vertices.length / 3) {
            faces.push(v1, v2, v3);
            
            // Add UV coordinates if available
            if (uv1 >= 0 && uv1 < uvs.length / 2 &&
                uv2 >= 0 && uv2 < uvs.length / 2 &&
                uv3 >= 0 && uv3 < uvs.length / 2) {
              faceUVs.push(
                uvs[uv1 * 2], uvs[uv1 * 2 + 1],
                uvs[uv2 * 2], uvs[uv2 * 2 + 1],
                uvs[uv3 * 2], uvs[uv3 * 2 + 1]
              );
            } else {
              // Add default UV coordinates if not available
              faceUVs.push(0, 0, 0, 1, 1, 1);
            }
          }
        }
      }
    }

    console.log('Parsed:', vertices.length / 3, 'vertices,', uvs.length / 2, 'UV coordinates,', faces.length / 3, 'triangles');

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    
    // Add UV coordinates if we have them
    if (faceUVs.length > 0) {
      geometry.setAttribute('uv', new THREE.Float32BufferAttribute(faceUVs, 2));
      console.log('Added UV coordinates to geometry');
    }
    
    geometry.setIndex(faces);
    geometry.computeVertexNormals();

    return geometry;
  };

  // Placeholder for PLY loader
  const loadPLYModel = async (plyData: string) => {
    console.log('PLY loading not yet implemented, using placeholder');
    await createPlaceholderModel();
  };

  // Placeholder for STL loader  
  const loadSTLModel = async (stlData: string) => {
    console.log('STL loading not yet implemented, using placeholder');
    await createPlaceholderModel();
  };



  // Cleanup
  const cleanup = () => {
    if (animationIdRef.current) {
      cancelAnimationFrame(animationIdRef.current);
    }
    if (controlsRef.current) {
      controlsRef.current.dispose();
      controlsRef.current = null;
    }
    if (rendererRef.current && mountRef.current) {
      mountRef.current.removeChild(rendererRef.current.domElement);
      rendererRef.current.dispose();
    }
    sceneRef.current = null;
    rendererRef.current = null;
    cameraRef.current = null;
  };

  useEffect(() => {
    if (isOpen) {
      const cleanupFn = initScene();
      loadModel();
      
      return () => {
        cleanupFn && cleanupFn();
        cleanup();
      };
    }
  }, [isOpen]);

  // Watch for material mode changes and reload model
  useEffect(() => {
    if (loadedAssets.objData && materialMode) {
      reloadModelWithMaterialMode();
    }
  }, [materialMode]);

  // Watch for material blend mode changes and reload model
  useEffect(() => {
    if (loadedAssets.objData && materialBlendMode) {
      reloadModelWithMaterialMode();
    }
  }, [materialBlendMode]);

  // Notify parent component when material data changes
  useEffect(() => {
    if (onMaterialDataChange && loadedAssets.objData) {
      onMaterialDataChange({
        materialMode,
        materialBlendMode,
        availableMaterials,
        onMaterialModeChange: setMaterialMode,
        onMaterialBlendModeChange: setMaterialBlendMode
      });
    }
  }, [materialMode, materialBlendMode, availableMaterials, loadedAssets.objData, onMaterialDataChange]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (mountRef.current && rendererRef.current && cameraRef.current) {
        const width = mountRef.current.clientWidth;
        const height = mountRef.current.clientHeight;
        
        cameraRef.current.aspect = width / height;
        cameraRef.current.updateProjectionMatrix();
        rendererRef.current.setSize(width, height);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isOpen]);

  return (
    <div className="w-full h-full relative overflow-hidden">
      {/* 3D Canvas Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-800 via-slate-900 to-black">
        <div 
          ref={mountRef} 
          className="w-full h-full"
          style={{ minHeight: '400px' }}
        />
      </div>

      {/* Modern Loading State */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/90 backdrop-blur">
          <div className="text-center">
            <div className="relative mb-6">
              <div className="w-16 h-16 border-4 border-purple-500/20 rounded-full mx-auto"></div>
              <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-16 h-16 border-4 border-transparent border-t-purple-500 rounded-full animate-spin"></div>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Loading 3D Model</h3>
            <p className="text-white/60 mb-1">Downloading and processing...</p>
            <p className="text-white/40 text-sm">{modelName}</p>
            <div className="mt-4 w-48 bg-white/10 rounded-full h-1 mx-auto">
              <div className="bg-gradient-to-r from-purple-500 to-purple-700 h-1 rounded-full animate-pulse" style={{ width: '70%' }}></div>
            </div>
          </div>
        </div>
      )}



      {/* Modern Error State */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/90 backdrop-blur">
          <div className="text-center max-w-md">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-red-500/20 flex items-center justify-center">
              <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">Failed to Load Model</h3>
            <p className="text-white/60 mb-6 leading-relaxed">{error}</p>
            <button
              onClick={loadModel}
              className="px-6 py-3 bg-gradient-to-r from-purple-500 to-purple-700 text-white rounded-lg hover:from-purple-600 hover:to-purple-800 transition-all font-medium flex items-center mx-auto"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Try Again
            </button>
          </div>
        </div>
      )}

      {/* Enhanced Controls Guide */}
      {!loading && !error && (
        <div className="absolute bottom-6 left-6 bg-black/20 backdrop-blur-md border border-white/10 rounded-xl p-4 text-white text-sm max-w-xs">
          <h4 className="font-semibold mb-3 flex items-center">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Controls
          </h4>
          <div className="space-y-2">
            <div className="flex items-center">
              <div className="w-2 h-2 bg-purple-400 rounded-full mr-3"></div>
              <span className="text-white/80">Left drag: Rotate</span>
            </div>
            <div className="flex items-center">
              <div className="w-2 h-2 bg-blue-400 rounded-full mr-3"></div>
              <span className="text-white/80">Right drag: Pan</span>
            </div>
            <div className="flex items-center">
                              <div className="w-2 h-2 bg-purple-400 rounded-full mr-3"></div>
              <span className="text-white/80">Scroll: Zoom</span>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-white/10 text-xs text-white/60">
            Format: OBJ • Engine: Three.js r179
          </div>
        </div>
      )}

      {/* Viewport Toolbar */}
      {!loading && !error && (
        <div className="absolute top-6 right-6 flex items-center space-x-2">
          <div className="bg-black/20 backdrop-blur-md border border-white/10 rounded-lg px-3 py-2 text-white text-sm">
            <span className="text-white/60">Viewport: </span>
            <span className="text-purple-400 font-medium">Active</span>
          </div>
          <button className="p-2 bg-black/20 backdrop-blur-md border border-white/10 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-all">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
};
