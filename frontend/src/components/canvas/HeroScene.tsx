"use client";

import { Float, OrbitControls, PointMaterial, Points } from "@react-three/drei";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

function LeadCore() {
  const group = useRef<THREE.Group>(null);
  const pointer = useThree((state) => state.pointer);
  useFrame((_, delta) => { if (!group.current) return; group.current.rotation.y += delta * 0.16; group.current.rotation.x = THREE.MathUtils.lerp(group.current.rotation.x, pointer.y * 0.16, 0.03); group.current.rotation.z = THREE.MathUtils.lerp(group.current.rotation.z, -pointer.x * 0.12, 0.03); });
  return <group ref={group}><mesh><icosahedronGeometry args={[1.65, 3]} /><meshStandardMaterial color="#7267ff" emissive="#3027a7" emissiveIntensity={1.8} roughness={0.32} metalness={0.7} wireframe /></mesh><mesh scale={0.84}><icosahedronGeometry args={[1.65, 2]} /><meshStandardMaterial color="#111d3c" emissive="#075985" emissiveIntensity={0.75} roughness={0.2} metalness={0.8} transparent opacity={0.82} /></mesh></group>;
}

function Dust() {
  const count = 180;
  const positions = useMemo(() => {
    const nextPositions = new Float32Array(count * 3);
    for (let index = 0; index < count; index += 1) { const seed = (value: number) => (Math.sin(value * 12.9898) * 43758.5453) % 1; const radius = 2.8 + Math.abs(seed(index + 1)) * 2.8; const theta = Math.abs(seed(index + 2)) * Math.PI * 2; const phi = Math.acos(2 * Math.abs(seed(index + 3)) - 1); nextPositions[index * 3] = radius * Math.sin(phi) * Math.cos(theta); nextPositions[index * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta); nextPositions[index * 3 + 2] = radius * Math.cos(phi); }
    return nextPositions;
  }, []);
  return <Points positions={positions} stride={3}><PointMaterial transparent color="#67e8f9" size={0.025} sizeAttenuation depthWrite={false} opacity={0.65} /></Points>;
}

export default function HeroScene() {
  return <Canvas className="hero-canvas" dpr={[1, 1.5]} camera={{ position: [0, 0, 7], fov: 38 }} gl={{ antialias: true, alpha: true }}><ambientLight intensity={0.55} /><directionalLight position={[3, 4, 5]} intensity={2.2} color="#a5b4fc" /><pointLight position={[-4, -2, 2]} intensity={14} distance={8} color="#06b6d4" /><Float speed={1.3} rotationIntensity={0.2} floatIntensity={0.35}><LeadCore /></Float><Dust /><OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.25} enableDamping dampingFactor={0.08} /></Canvas>;
}