/* ==========================================================================
   J.A.R.V.I.S. — NEURAL KNOWLEDGE GRAPH & VOICE ASSISTANT ENGINE (484 NODES)
   ========================================================================== */

(function () {
  'use strict';

  /* --------------------------------------------------------------------------
     AUDIO SYNTHESIZER (Web Audio API — procedural sci-fi sounds)
     -------------------------------------------------------------------------- */
  const SoundFX = (() => {
    let ctx = null;
    let enabled = true;

    function getCtx() {
      if (!ctx) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) ctx = new AudioCtx();
      }
      if (ctx && ctx.state === 'suspended') {
        ctx.resume().catch(() => {});
      }
      return ctx;
    }

    function beep(freq = 880, duration = 0.08, type = 'sine', gainVal = 0.08) {
      if (!enabled) return;
      try {
        const c = getCtx();
        if (!c) return;
        const osc = c.createOscillator();
        const g = c.createGain();
        osc.type = type;
        osc.frequency.setValueAtTime(freq, c.currentTime);
        g.gain.setValueAtTime(gainVal, c.currentTime);
        g.gain.exponentialRampToValueAtTime(0.0001, c.currentTime + duration);
        osc.connect(g);
        g.connect(c.destination);
        osc.start();
        osc.stop(c.currentTime + duration);
      } catch (_) {}
    }

    function chime(freqs = [523.25, 659.25, 783.99, 1046.50]) {
      if (!enabled) return;
      freqs.forEach((f, idx) => {
        setTimeout(() => beep(f, 0.18, 'triangle', 0.07), idx * 55);
      });
    }

    function hum() {
      if (!enabled) return;
      beep(110, 0.35, 'sawtooth', 0.03);
    }

    function toggle() {
      enabled = !enabled;
      return enabled;
    }

    return { beep, chime, hum, toggle, isEnabled: () => enabled };
  })();

  /* --------------------------------------------------------------------------
     CATEGORIES & CONFIGURATION (Exactly matching prompt)
     🟡 Concepts: 23
     🟣 Suites: 13
     🔵 Skills: 197
     🩷 Tools: 19
     🟠 Worlds: 15
     🟢 Notes: 25
     ⚪ Files: 192
     Total: 484 nodes!
     -------------------------------------------------------------------------- */
  const CATEGORIES = {
    Concepts: { color: '#ffcf25', glow: 'rgba(255, 207, 37, 0.65)', icon: '🟡', name: 'Concepts', targetCount: 23 },
    Suites:   { color: '#b366ff', glow: 'rgba(179, 102, 255, 0.65)', icon: '🟣', name: 'Suites',   targetCount: 13 },
    Skills:   { color: '#00d2ff', glow: 'rgba(0, 210, 255, 0.65)',   icon: '🔵', name: 'Skills',   targetCount: 197 },
    Tools:    { color: '#ff4d94', glow: 'rgba(255, 77, 148, 0.65)',  icon: '🩷', name: 'Tools',    targetCount: 19 },
    Worlds:   { color: '#ff8c1a', glow: 'rgba(255, 140, 26, 0.65)',  icon: '🟠', name: 'Worlds',   targetCount: 15 },
    Notes:    { color: '#10e885', glow: 'rgba(16, 232, 133, 0.65)',  icon: '🟢', name: 'Notes',    targetCount: 25 },
    Files:    { color: '#ffffff', glow: 'rgba(255, 255, 255, 0.85)',  icon: '⚪', name: 'Files',    targetCount: 192 },
  };

  /* --------------------------------------------------------------------------
     GENERATE GRAPH DATA (484 Nodes + ~1,850 Connecting Links)
     -------------------------------------------------------------------------- */
  function generateGraphData() {
    const nodes = [];
    const links = [];
    let idCounter = 1;

    // Helper to add node
    function addNode(name, category, size, x, y, z, desc = '', isKeyHub = false) {
      const node = {
        id: `node-${idCounter++}`,
        name,
        category,
        size,
        baseSize: size,
        x, y, z,
        vx: 0, vy: 0, vz: 0,
        desc: desc || `${category} node in J.A.R.V.I.S. neural matrix.`,
        isKeyHub,
        linksCount: 0,
        active: true,
      };
      nodes.push(node);
      return node;
    }

    // 1. 🟡 CONCEPTS (23 nodes) — Prominent hubs in center and left-center
    const conceptNames = [
      { name: 'AI Workshop', size: 24, x: -60, y: 15, z: 10, isHub: true, desc: 'Central neural engineering nexus for autonomous multi-agent creation and LLM distillation.' },
      { name: 'Claude', size: 20, x: -120, y: -45, z: -25, isHub: true, desc: 'Advanced reasoning, symbolic logic, and deep code synthesis engine.' },
      { name: 'Cognitive Matrix', size: 16, x: 20, y: -80, z: 30 },
      { name: 'Neural Embeddings', size: 15, x: -180, y: 60, z: -15 },
      { name: 'Quantum Heuristics', size: 14, x: 80, y: 40, z: -50 },
      { name: 'Autonomous Agents', size: 16, x: -90, y: 110, z: 40 },
      { name: 'Multimodal Perception', size: 15, x: 10, y: 130, z: -20 },
      { name: 'Semantic Reasoning', size: 14, x: -40, y: -130, z: 15 },
      { name: 'Vector Retrieval', size: 15, x: -150, y: -100, z: -40 },
      { name: 'Spatial Computing', size: 14, x: 60, y: -40, z: 60 },
      { name: 'Decentralized Core', size: 13, x: -10, y: -30, z: -80 },
      { name: 'Context Synthesis', size: 14, x: -110, y: 170, z: -10 },
      { name: 'Bio-Digital Feedback', size: 13, x: 110, y: 90, z: 25 },
      { name: 'Meta-Prompting', size: 13, x: -75, y: -70, z: 50 },
      { name: 'Action Planner', size: 14, x: -200, y: 10, z: 35 },
      { name: 'Self-Correction', size: 13, x: 45, y: 80, z: -60 },
      { name: 'Logic Primitives', size: 12, x: -130, y: -160, z: 20 },
      { name: 'Pattern Synthesizer', size: 13, x: 130, y: -90, z: -30 },
      { name: 'Emergent Swarm', size: 14, x: -220, y: 90, z: -60 },
      { name: 'Symbolic Math Core', size: 12, x: 95, y: -140, z: 40 },
      { name: 'Temporal Memory', size: 13, x: -30, y: 70, z: 90 },
      { name: 'Audio Latency Theory', size: 12, x: 70, y: 160, z: 10 },
      { name: 'Zero-Shot Adaptor', size: 12, x: -160, y: -20, z: 80 },
    ];
    const conceptNodes = conceptNames.map(c => addNode(c.name, 'Concepts', c.size, c.x, c.y, c.z, c.desc, c.isHub));

    // 2. 🟣 SUITES (13 nodes) — Specific packages & suites
    const suiteNames = [
      { name: 'GEO Suite', size: 18, x: 100, y: 10, z: -10, isHub: true, desc: 'Geospatial intelligence, satellite telemetry, and coordinate triangulation suite.' },
      { name: 'CiteVue', size: 17, x: 140, y: -60, z: 20, isHub: true, desc: 'Academic literature mapping, semantic citations, and research synthesis suite.' },
      { name: 'Dev Agent Suite', size: 15, x: -140, y: 75, z: 55 },
      { name: 'OSINT Suite', size: 15, x: 160, y: 80, z: -40 },
      { name: 'Vision Matrix Suite', size: 15, x: 40, y: 110, z: 70 },
      { name: 'Holo Lab Suite', size: 16, x: 120, y: -120, z: -60 },
      { name: 'Cyber Defense Suite', size: 14, x: -80, y: -180, z: -50 },
      { name: 'Audio Synthesizer Suite', size: 14, x: 90, y: 140, z: 45 },
      { name: 'FaceID LBPH Suite', size: 15, x: -20, y: 160, z: -45 },
      { name: 'Workflow Automation', size: 13, x: -180, y: 140, z: 10 },
      { name: 'Hardware Bridge Suite', size: 14, x: 50, y: -160, z: -15 },
      { name: 'Quantum Sim Suite', size: 14, x: 170, y: -20, z: 80 },
      { name: 'Neural Memory Suite', size: 14, x: -60, y: 40, z: -110 },
    ];
    const suiteNodes = suiteNames.map(s => addNode(s.name, 'Suites', s.size, s.x, s.y, s.z, s.desc, s.isHub));

    // 3. 🔵 SKILLS (197 nodes) — Huge dense cluster concentrated on the LEFT side
    const prominentSkills = [
      'Speech Recognition STT', 'LBPH Face Recognition', 'YuNet Neural Detection', 'Browser Control',
      'Computer Vision OCR', 'Python Code Synthesizer', 'Fast Fourier Audio Scope', 'Pose Tracker 3D',
      'Network Scanner', 'Flight Route Finder', 'Weather Telemetry', 'Discord Controller',
      'Crypto Oracle Watcher', 'YouTube Transcriber', 'File Controller API', 'M5Stick IoT Handler',
      'Vocal Tone Modulator', 'System Health Telemetry', 'Git Commit Automator', 'Spatial Triangulation',
      'Database Query Engine', 'AES-256 Crypto Mesh', 'Web Scraping Matrix', 'Zero-Day Shield',
      'Mic Audio FFT Stream', 'Screen Processor AI', 'Vector Memory Query', 'Task Queue Manager',
      'Bluetooth AVRCP Hook', 'Dev Agent Sandbox', 'Holo Blueprint Engine', 'Social OSINT Parser',
      'Gesture Landmark Est', 'Proactive Trigger Loop', 'Camera Face Vault', 'Neural Text TTS'
    ];
    const skillNodes = [];
    // Left cluster center: x: -240, y: 0, z: 0 with radius ~220
    for (let i = 0; i < 197; i++) {
      const name = i < prominentSkills.length ? prominentSkills[i] : `Skill: Neural Routine #${i + 1}`;
      const theta = Math.random() * Math.PI * 2;
      const phi = (Math.random() - 0.5) * Math.PI;
      const rad = 60 + Math.random() * 220;
      const x = -230 + rad * Math.cos(theta) * Math.cos(phi);
      const y = (Math.random() - 0.5) * 320 + rad * Math.sin(phi) * 0.7;
      const z = rad * Math.sin(theta) * Math.cos(phi) * 0.9;
      const size = i < 12 ? (7 + Math.random() * 4) : (3.5 + Math.random() * 3);
      skillNodes.push(addNode(name, 'Skills', size, x, y, z, `Autonomous algorithmic skill routine #${i + 1}`));
    }

    // 4. 🩷 TOOLS (19 nodes) — Utilities in upper and center area
    const toolNames = [
      { name: 'YouTube Channel', size: 15, x: -30, y: -110, z: 70, isHub: true, desc: 'Multimedia feed automation and video stream processing tool.' },
      { name: 'Video', size: 14, x: 20, y: -130, z: 90, isHub: true, desc: 'Real-time video encoder, frame analyzer, and spatial object tracker.' },
      { name: 'Web Search Engine', size: 13, x: -90, y: -80, z: -70 },
      { name: 'Code Assistant', size: 14, x: -140, y: -40, z: 40 },
      { name: 'File Vault', size: 13, x: 40, y: -70, z: -85 },
      { name: 'Pose Worker', size: 12, x: -10, y: 140, z: 60 },
      { name: 'Holo Visualizer', size: 13, x: 130, y: -80, z: -40 },
      { name: 'Terminal Bridge', size: 12, x: -110, y: 130, z: -50 },
      { name: 'Audio FFT Scope', size: 12, x: 70, y: 120, z: 20 },
      { name: 'Color Calibrator', size: 11, x: 150, y: 40, z: 50 },
      { name: 'Package Builder', size: 12, x: -160, y: 90, z: -20 },
      { name: 'API Proxy Gateway', size: 12, x: 10, y: -40, z: 110 },
      { name: 'Task Scheduler', size: 12, x: -50, y: -150, z: -20 },
      { name: 'Log Streamer', size: 11, x: 80, y: -120, z: 30 },
      { name: 'Markdown Parser', size: 11, x: 160, y: -110, z: 15 },
      { name: 'Image Synthesizer', size: 13, x: -20, y: 90, z: -90 },
      { name: 'Speech Synthesizer', size: 13, x: 60, y: 170, z: -30 },
      { name: 'Sensor Telemetry', size: 12, x: 110, y: 110, z: -70 },
      { name: 'Diagnostic Probe', size: 12, x: -80, y: 50, z: 120 },
    ];
    const toolNodes = toolNames.map(t => addNode(t.name, 'Tools', t.size, t.x, t.y, t.z, t.desc, t.isHub));

    // 5. 🟠 WORLDS (15 nodes) — Virtual domains & environments in center
    const worldNames = [
      { name: 'GEO', size: 17, x: 85, y: -15, z: 15, isHub: true, desc: 'Planetary geospatial environment and earth observation coordinate grid.' },
      { name: 'Projects', size: 16, x: -10, y: 45, z: 35, isHub: true, desc: 'Portfolio of active high-tech research, automation prototypes, and builds.' },
      { name: 'Simulation Grid', size: 14, x: 130, y: -40, z: -80 },
      { name: 'Cyber Space Core', size: 14, x: -70, y: -90, z: 110 },
      { name: 'Robotics Grid', size: 14, x: 110, y: 70, z: 60 },
      { name: 'Satellite Matrix', size: 13, x: 150, y: 20, z: -30 },
      { name: 'IoT Swarm Realm', size: 13, x: 40, y: -140, z: -60 },
      { name: 'Digital Twin City', size: 13, x: 90, y: -90, z: 85 },
      { name: 'Metaverse Nexus', size: 12, x: 170, y: -70, z: 30 },
      { name: 'Smart Home Grid', size: 12, x: 20, y: 100, z: 100 },
      { name: 'Sound Lab Studio', size: 13, x: 100, y: 150, z: -10 },
      { name: 'Vision Sphere', size: 13, x: -30, y: 130, z: -70 },
      { name: 'Autonomous Fleet', size: 12, x: 140, y: 100, z: 20 },
      { name: 'Global News Feed', size: 12, x: 60, y: -60, z: -120 },
      { name: 'Quantum Mesh Realm', size: 13, x: -50, y: -30, z: -130 },
    ];
    const worldNodes = worldNames.map(w => addNode(w.name, 'Worlds', w.size, w.x, w.y, w.z, w.desc, w.isHub));

    // 6. 🟢 NOTES (25 nodes) — Compact clusters on the RIGHT and center-right
    const noteNames = [
      { name: 'AI Children’s Books', size: 17, x: 200, y: 15, z: 20, isHub: true, desc: 'Creative generative storytelling, character lore, and illustrated children book project notes.' },
      { name: 'Notes', size: 16, x: 170, y: -35, z: -15, isHub: true, desc: 'Primary repository of research memos, sprint logs, and architectural RFCs.' },
      { name: 'Story Arc Draft 4', size: 11, x: 225, y: 35, z: 30 },
      { name: 'Character Lore: Jax & Spark', size: 11, x: 215, y: -10, z: 45 },
      { name: 'Illustration Prompt Set', size: 11, x: 235, y: 0, z: 10 },
      { name: 'Children Voice Tone Spec', size: 10, x: 190, y: 55, z: 40 },
      { name: 'Project Blueprint Alpha', size: 13, x: 160, y: -80, z: -30 },
      { name: 'Weekly Sprint Log 2026', size: 12, x: 140, y: -65, z: 10 },
      { name: 'Architecture RFC-42', size: 12, x: 180, y: -60, z: 50 },
      { name: 'Voice Synthesis Research', size: 12, x: 150, y: 80, z: -15 },
      { name: 'FaceID Calibration Memo', size: 11, x: 175, y: 65, z: 25 },
      { name: 'Vector DB Latency Test', size: 11, x: 130, y: 40, z: 80 },
      { name: 'Prompt Engineering Guide', size: 12, x: 195, y: -85, z: -10 },
      { name: 'Holo Lab Parts Catalog Spec', size: 12, x: 165, y: -110, z: -45 },
      { name: 'Neural Graph Schema v2', size: 12, x: 125, y: -20, z: -90 },
      { name: 'Meeting Summary: Core Team', size: 10, x: 210, y: -45, z: -55 },
      { name: 'Autonomous Agent Safety', size: 11, x: 145, y: 115, z: 40 },
      { name: 'Robotics Telemetry Log', size: 11, x: 185, y: 105, z: -40 },
      { name: 'Security Audit: Pass 1', size: 11, x: 115, y: -120, z: 25 },
      { name: 'GEOINT Satellite Bounds', size: 12, x: 135, y: 15, z: -60 },
      { name: 'Color Palette Scheme Cyan', size: 10, x: 240, y: -25, z: 15 },
      { name: 'Audio Book Script #2', size: 11, x: 220, y: 60, z: -10 },
      { name: 'TTS Voice Model Audition', size: 11, x: 170, y: 130, z: 10 },
      { name: 'Hardware BOM M5Stick', size: 10, x: 155, y: -140, z: -20 },
      { name: 'Roadmap Horizon 2027', size: 12, x: 205, y: 90, z: 35 },
    ];
    const noteNodes = noteNames.map(n => addNode(n.name, 'Notes', n.size, n.x, n.y, n.z, n.desc, n.isHub));

    // 7. ⚪ FILES (192 nodes) — Bright white luminescent nodes scattered across space
    const prominentFiles = [
      'Build Cell Series', 'main.py', 'dashboard/server.py', 'ui.py', 'holo_lab.py',
      'face_id.py', 'stt.py', 'tts.py', 'model_router.py', 'api_keys.json',
      'manifest.webmanifest', 'app.html', 'style.css', 'm5stick_firmware.ino',
      'geoint_engine.py', 'pose_tracker.py', 'voice_features.py', 'background_monitor.py',
      'browser_control.py', 'code_helper.py', 'network_scanner.py', 'social_osint.py'
    ];
    const fileNodes = [];
    for (let i = 0; i < 192; i++) {
      const isNamed = i < prominentFiles.length;
      const name = isNamed ? prominentFiles[i] : `file_${(i + 1).toString().padStart(3, '0')}.dat`;
      const theta = Math.random() * Math.PI * 2;
      const phi = (Math.random() - 0.5) * Math.PI;
      const rad = 80 + Math.random() * 260;
      const x = rad * Math.cos(theta) * Math.cos(phi) * 0.95;
      const y = (Math.random() - 0.5) * 360;
      const z = rad * Math.sin(theta) * Math.cos(phi);
      const size = isNamed ? (i === 0 ? 16 : (8 + Math.random() * 4)) : (2.8 + Math.random() * 2.5);
      fileNodes.push(addNode(name, 'Files', size, x, y, z, `File buffer resource ${name}`, isNamed && i === 0));
    }

    // ------------------------------------------------------------------------
    // BUILD NETWORK LINKS (~1,850 links)
    // ------------------------------------------------------------------------
    const aiWorkshop = conceptNodes[0]; // AI Workshop
    const claudeNode = conceptNodes[1]; // Claude
    const geoSuite   = suiteNodes[0];   // GEO Suite
    const citeVue    = suiteNodes[1];   // CiteVue
    const geoWorld   = worldNodes[0];   // GEO
    const projWorld  = worldNodes[1];   // Projects
    const booksNote  = noteNodes[0];    // AI Children's Books
    const notesHub   = noteNodes[1];    // Notes
    const buildCell  = fileNodes[0];    // Build Cell Series
    const ytChannel  = toolNodes[0];    // YouTube Channel
    const videoTool  = toolNodes[1];    // Video

    const linkSet = new Set();
    function createLink(source, target, weight = 1) {
      if (!source || !target || source === target) return;
      const key = source.id < target.id ? `${source.id}_${target.id}` : `${target.id}_${source.id}`;
      if (linkSet.has(key)) return;
      linkSet.add(key);
      links.push({
        source,
        target,
        weight,
        pulseOffset: Math.random(),
        pulseSpeed: 0.003 + Math.random() * 0.006,
      });
      source.linksCount++;
      target.linksCount++;
    }

    // Major radiant connections from "AI Workshop" (hundreds of lines to blue skills)
    skillNodes.forEach((s, idx) => {
      if (idx % 2 === 0 || idx < 50) createLink(aiWorkshop, s, 0.85);
      if (idx % 3 === 0 || idx < 30) createLink(claudeNode, s, 0.75);
    });

    // Cross-connect skills into dense neural mesh on the left
    for (let i = 0; i < skillNodes.length; i++) {
      const neighborCount = 4 + (i % 5);
      for (let k = 1; k <= neighborCount; k++) {
        const targetIdx = (i + k * 3 + 1) % skillNodes.length;
        createLink(skillNodes[i], skillNodes[targetIdx], 0.35);
      }
    }

    // Connect Concepts
    conceptNodes.forEach((c, idx) => {
      if (c !== aiWorkshop) createLink(aiWorkshop, c, 0.9);
      if (c !== claudeNode && idx % 2 === 0) createLink(claudeNode, c, 0.7);
      createLink(c, conceptNodes[(idx + 1) % conceptNodes.length], 0.5);
    });

    // Connect Suites (e.g. GEO Suite to GEO world, AI Workshop)
    createLink(geoSuite, geoWorld, 1.0);
    createLink(geoSuite, aiWorkshop, 0.8);
    createLink(citeVue, claudeNode, 0.9);
    createLink(citeVue, notesHub, 0.85);
    suiteNodes.forEach((s, idx) => {
      createLink(s, aiWorkshop, 0.7);
      createLink(s, conceptNodes[idx % conceptNodes.length], 0.6);
      if (idx < toolNodes.length) createLink(s, toolNodes[idx], 0.5);
    });

    // Connect Worlds
    createLink(geoWorld, projWorld, 0.8);
    createLink(projWorld, aiWorkshop, 0.9);
    worldNodes.forEach((w, idx) => {
      createLink(w, projWorld, 0.6);
      createLink(w, conceptNodes[(idx + 3) % conceptNodes.length], 0.5);
    });

    // Connect Tools (YouTube Channel, Video, etc.)
    createLink(ytChannel, videoTool, 0.95);
    createLink(ytChannel, aiWorkshop, 0.75);
    createLink(videoTool, aiWorkshop, 0.75);
    toolNodes.forEach((t, idx) => {
      createLink(t, aiWorkshop, 0.55);
      createLink(t, skillNodes[idx * 5 % skillNodes.length], 0.5);
    });

    // Connect Notes Cluster (AI Children's Books, Notes, story drafts)
    createLink(booksNote, notesHub, 0.95);
    createLink(booksNote, ytChannel, 0.6);
    createLink(booksNote, aiWorkshop, 0.65);
    noteNodes.forEach((n, idx) => {
      if (n !== booksNote && idx < 6) createLink(booksNote, n, 0.8);
      createLink(n, notesHub, 0.7);
      if (idx % 3 === 0) createLink(n, claudeNode, 0.5);
    });

    // Connect Files (Build Cell Series, main.py, etc.)
    createLink(buildCell, projWorld, 0.9);
    createLink(buildCell, aiWorkshop, 0.85);
    fileNodes.forEach((f, idx) => {
      if (idx < 25) {
        createLink(f, aiWorkshop, 0.6);
        createLink(f, suiteNodes[idx % suiteNodes.length], 0.5);
      }
      // Cluster files to neighboring files
      const neighbor = fileNodes[(idx + 7) % fileNodes.length];
      createLink(f, neighbor, 0.3);
      if (idx % 4 === 0) {
        createLink(f, conceptNodes[idx % conceptNodes.length], 0.35);
      }
    });

    return { nodes, links };
  }

  /* --------------------------------------------------------------------------
     3D KNOWLEDGE GRAPH RENDERING ENGINE
     -------------------------------------------------------------------------- */
  class KnowledgeGraph3D {
    constructor(canvas, data) {
      this.canvas = canvas;
      this.ctx = canvas.getContext('2d');
      this.nodes = data.nodes;
      this.links = data.links;

      // Filter state
      this.activeCategories = new Set(Object.keys(CATEGORIES));
      this.searchQuery = '';
      this.selectedNode = null;
      this.hoveredNode = null;

      // Layout Modes: 'galaxy', 'sphere', 'clusters', 'force'
      this.layoutMode = 'galaxy';

      // 3D Camera coordinates
      this.cam = {
        x: 0,
        y: 0,
        z: 920,
        targetX: 0,
        targetY: 0,
        targetZ: 920,
        rotX: -0.12,
        rotY: 0.28,
        rotZ: 0,
        targetRotX: -0.12,
        targetRotY: 0.28,
        autoRotate: true,
        fov: 700,
      };

      // 3D Cosmic Starfield Particles
      this.stars = [];
      for (let i = 0; i < 280; i++) {
        this.stars.push({
          x: (Math.random() - 0.5) * 2200,
          y: (Math.random() - 0.5) * 2200,
          z: (Math.random() - 0.5) * 2200,
          size: 0.8 + Math.random() * 1.6,
          alpha: 0.2 + Math.random() * 0.6,
          twinkleSpeed: 0.01 + Math.random() * 0.02,
        });
      }

      // Interaction drag tracking
      this.isDragging = false;
      this.dragButton = 0; // 0 = left, 2 = right
      this.lastMouseX = 0;
      this.lastMouseY = 0;
      this.mouseScreenX = -9999;
      this.mouseScreenY = -9999;

      this.initEvents();
      this.resize();
      this.animate = this.animate.bind(this);
      requestAnimationFrame(this.animate);
    }

    resize() {
      const rect = this.canvas.parentElement.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      this.width = rect.width;
      this.height = rect.height;
      this.canvas.width = this.width * dpr;
      this.canvas.height = this.height * dpr;
      this.ctx.scale(dpr, dpr);
    }

    initEvents() {
      window.addEventListener('resize', () => this.resize());

      this.canvas.addEventListener('mousedown', (e) => {
        this.isDragging = true;
        this.dragButton = e.button;
        this.lastMouseX = e.clientX;
        this.lastMouseY = e.clientY;
      });

      window.addEventListener('mouseup', () => {
        this.isDragging = false;
      });

      this.canvas.addEventListener('contextmenu', (e) => e.preventDefault());

      this.canvas.addEventListener('mousemove', (e) => {
        const rect = this.canvas.getBoundingClientRect();
        this.mouseScreenX = e.clientX - rect.left;
        this.mouseScreenY = e.clientY - rect.top;

        if (this.isDragging) {
          const dx = e.clientX - this.lastMouseX;
          const dy = e.clientY - this.lastMouseY;
          this.lastMouseX = e.clientX;
          this.lastMouseY = e.clientY;

          if (this.dragButton === 0 && !e.shiftKey) {
            // Left click: Orbit Rotation
            this.cam.targetRotY += dx * 0.005;
            this.cam.targetRotX -= dy * 0.005;
            // clamp rotX
            this.cam.targetRotX = Math.max(-Math.PI / 2.1, Math.min(Math.PI / 2.1, this.cam.targetRotX));
          } else {
            // Right click or Shift+Left: Pan
            const panScale = this.cam.z / 900;
            this.cam.targetX -= dx * 0.8 * panScale;
            this.cam.targetY -= dy * 0.8 * panScale;
          }
        }

        this.checkHover();
      });

      this.canvas.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY * 0.9;
        this.cam.targetZ = Math.max(220, Math.min(2400, this.cam.targetZ + delta));
      }, { passive: false });

      // Touch events
      let lastTouchDist = 0;
      this.canvas.addEventListener('touchstart', (e) => {
        if (e.touches.length === 1) {
          this.isDragging = true;
          this.dragButton = 0;
          this.lastMouseX = e.touches[0].clientX;
          this.lastMouseY = e.touches[0].clientY;
        } else if (e.touches.length === 2) {
          this.isDragging = false;
          const dx = e.touches[0].clientX - e.touches[1].clientX;
          const dy = e.touches[0].clientY - e.touches[1].clientY;
          lastTouchDist = Math.hypot(dx, dy);
        }
      });

      this.canvas.addEventListener('touchmove', (e) => {
        if (e.touches.length === 1 && this.isDragging) {
          const dx = e.touches[0].clientX - this.lastMouseX;
          const dy = e.touches[0].clientY - this.lastMouseY;
          this.lastMouseX = e.touches[0].clientX;
          this.lastMouseY = e.touches[0].clientY;
          this.cam.targetRotY += dx * 0.007;
          this.cam.targetRotX -= dy * 0.007;
        } else if (e.touches.length === 2) {
          const dx = e.touches[0].clientX - e.touches[1].clientX;
          const dy = e.touches[0].clientY - e.touches[1].clientY;
          const dist = Math.hypot(dx, dy);
          if (lastTouchDist > 0) {
            const deltaDist = lastTouchDist - dist;
            this.cam.targetZ = Math.max(220, Math.min(2400, this.cam.targetZ + deltaDist * 2.5));
          }
          lastTouchDist = dist;
        }
      });

      this.canvas.addEventListener('touchend', () => {
        this.isDragging = false;
        lastTouchDist = 0;
      });

      // Click to select node
      this.canvas.addEventListener('click', () => {
        if (this.hoveredNode) {
          this.selectNode(this.hoveredNode);
          SoundFX.beep(660, 0.12, 'sine', 0.1);
        }
      });
    }

    checkHover() {
      let closestNode = null;
      let minHitDist = 18;

      for (let i = this.nodes.length - 1; i >= 0; i--) {
        const n = this.nodes[i];
        if (!n.projected || !n.active) continue;
        const dx = this.mouseScreenX - n.projected.sx;
        const dy = this.mouseScreenY - n.projected.sy;
        const dist = Math.hypot(dx, dy);
        const hitRadius = Math.max(12, n.projected.r * 1.5);
        if (dist < hitRadius && dist < minHitDist) {
          minHitDist = dist;
          closestNode = n;
        }
      }

      if (closestNode !== this.hoveredNode) {
        this.hoveredNode = closestNode;
        if (closestNode) {
          this.canvas.style.cursor = 'pointer';
          this.showTooltip(closestNode);
          SoundFX.beep(1200, 0.03, 'sine', 0.04);
        } else {
          this.canvas.style.cursor = this.isDragging ? 'grabbing' : 'grab';
          this.hideTooltip();
        }
      }
    }

    showTooltip(node) {
      const el = document.getElementById('nodeTooltip');
      if (!el) return;
      el.style.display = 'block';
      el.style.left = `${Math.min(this.width - 200, Math.max(10, node.projected.sx + 15))}px`;
      el.style.top = `${Math.min(this.height - 120, Math.max(10, node.projected.sy - 20))}px`;

      const catMeta = CATEGORIES[node.category] || {};
      el.querySelector('.tooltip-cat-dot').style.background = catMeta.color || '#fff';
      el.querySelector('.tooltip-cat-name').textContent = `${catMeta.icon || ''} ${node.category}`;
      el.querySelector('.tooltip-title').textContent = node.name;
      el.querySelector('.tooltip-links').textContent = node.linksCount;
      el.querySelector('.tooltip-cluster').textContent = node.isKeyHub ? 'Central Hub' : node.category;
    }

    hideTooltip() {
      const el = document.getElementById('nodeTooltip');
      if (el) el.style.display = 'none';
    }

    selectNode(node) {
      this.selectedNode = node;
      // Fly camera smoothly toward node
      this.cam.targetX = node.x * 0.7;
      this.cam.targetY = node.y * 0.7;
      this.cam.targetZ = Math.max(380, this.cam.z * 0.75);

      // Update HUD telemetry
      const hudActive = document.getElementById('hudActiveNode');
      if (hudActive) hudActive.textContent = `${node.name} [${node.category}]`;
      const hudCluster = document.getElementById('hudActiveCluster');
      if (hudCluster) hudCluster.textContent = node.isKeyHub ? 'Core Command Nexus' : `${node.category} Cluster`;

      // Open node details inspector
      this.openInspector(node);
    }

    openInspector(node) {
      const drawer = document.getElementById('nodeInspectorDrawer');
      if (!drawer) return;
      drawer.classList.add('open');

      const catMeta = CATEGORIES[node.category] || {};
      const catBadge = document.getElementById('inspectorCatBadge');
      if (catBadge) {
        catBadge.textContent = `${catMeta.icon || ''} ${node.category}`;
        catBadge.style.color = catMeta.color || '#00f0ff';
        catBadge.style.borderColor = catMeta.color || '#00f0ff';
        catBadge.style.backgroundColor = `${catMeta.color}22`;
      }
      const idBadge = document.getElementById('inspectorNodeId');
      if (idBadge) idBadge.textContent = node.id.toUpperCase();

      const titleEl = document.getElementById('inspectorTitle');
      if (titleEl) titleEl.textContent = node.name;

      const descEl = document.getElementById('inspectorDesc');
      if (descEl) descEl.textContent = node.desc;

      const catEl = document.getElementById('inspectorCategory');
      if (catEl) catEl.textContent = node.category;

      const linksEl = document.getElementById('inspectorLinkCount');
      if (linksEl) linksEl.textContent = node.linksCount;

      const posEl = document.getElementById('inspectorPos');
      if (posEl) posEl.textContent = `X:${Math.round(node.x)} Y:${Math.round(node.y)} Z:${Math.round(node.z)}`;

      const priorityEl = document.getElementById('inspectorPriority');
      if (priorityEl) {
        priorityEl.textContent = node.isKeyHub ? 'ALPHA CORE [LEVEL 1]' : (node.linksCount > 15 ? 'BETA HUB [LEVEL 2]' : 'LEAF NODE [LEVEL 3]');
      }

      // Populate connected nodes
      const listEl = document.getElementById('inspectorConnectedList');
      if (listEl) {
        listEl.innerHTML = '';
        const connected = [];
        this.links.forEach(l => {
          if (l.source === node) connected.push(l.target);
          else if (l.target === node) connected.push(l.source);
        });
        connected.slice(0, 16).forEach(targetNode => {
          const chip = document.createElement('button');
          chip.className = 'connected-node-chip';
          const tCat = CATEGORIES[targetNode.category] || {};
          chip.innerHTML = `<span style="color:${tCat.color}">${tCat.icon || '●'}</span> ${targetNode.name}`;
          chip.addEventListener('click', () => {
            this.selectNode(targetNode);
            SoundFX.beep(780, 0.08, 'sine', 0.08);
          });
          listEl.appendChild(chip);
        });
      }
    }

    focusActiveNode() {
      if (this.selectedNode) {
        this.cam.targetX = this.selectedNode.x;
        this.cam.targetY = this.selectedNode.y;
        this.cam.targetZ = 420;
        SoundFX.chime([523, 659, 783]);
      }
    }

    filterCategory(catName) {
      if (this.activeCategories.has(catName) && this.activeCategories.size === 1) {
        // Reset to all
        this.activeCategories = new Set(Object.keys(CATEGORIES));
      } else if (this.activeCategories.size === Object.keys(CATEGORIES).length) {
        // Isolate single
        this.activeCategories = new Set([catName]);
      } else if (this.activeCategories.has(catName)) {
        this.activeCategories.delete(catName);
      } else {
        this.activeCategories.add(catName);
      }
      this.updateNodeVisibility();
    }

    resetFilters() {
      this.activeCategories = new Set(Object.keys(CATEGORIES));
      this.searchQuery = '';
      this.updateNodeVisibility();
    }

    search(query) {
      this.searchQuery = query.toLowerCase().trim();
      this.updateNodeVisibility();

      if (this.searchQuery) {
        const match = this.nodes.find(n => n.name.toLowerCase().includes(this.searchQuery));
        if (match) {
          this.selectNode(match);
        }
      }
    }

    updateNodeVisibility() {
      this.nodes.forEach(n => {
        const catMatch = this.activeCategories.has(n.category);
        const searchMatch = !this.searchQuery || n.name.toLowerCase().includes(this.searchQuery) || n.category.toLowerCase().includes(this.searchQuery);
        n.active = catMatch && searchMatch;
      });

      // Update UI legend item dims
      document.querySelectorAll('.legend-item').forEach(el => {
        const cat = el.dataset.cat;
        if (this.activeCategories.has(cat)) {
          el.classList.remove('dimmed');
        } else {
          el.classList.add('dimmed');
        }
      });
    }

    setLayoutMode(mode) {
      this.layoutMode = mode;
      SoundFX.chime([440, 554, 659, 880]);
    }

    resetCamera() {
      this.cam.targetX = 0;
      this.cam.targetY = 0;
      this.cam.targetZ = 920;
      this.cam.targetRotX = -0.12;
      this.cam.targetRotY = 0.28;
      this.selectedNode = null;
      SoundFX.beep(440, 0.15, 'sine', 0.08);
    }

    // 3D Projection Math
    project(x, y, z) {
      // 1. Rotate Y (Yaw)
      const cosY = Math.cos(this.cam.rotY);
      const sinY = Math.sin(this.cam.rotY);
      const x1 = x * cosY - z * sinY;
      const z1 = z * cosY + x * sinY;

      // 2. Rotate X (Pitch)
      const cosX = Math.cos(this.cam.rotX);
      const sinX = Math.sin(this.cam.rotX);
      const y2 = y * cosX - z1 * sinX;
      const z2 = z1 * cosX + y * sinX;

      // 3. Camera Pan offset
      const cx = x1 - this.cam.x;
      const cy = y2 - this.cam.y;
      const cz = z2 + this.cam.z;

      if (cz <= 10) return null; // Behind camera

      const scale = this.cam.fov / cz;
      const sx = cx * scale + this.width / 2;
      const sy = cy * scale + this.height / 2;

      return { sx, sy, scale, zDepth: cz };
    }

    animate() {
      // Smooth camera interpolation (dampening)
      this.cam.x += (this.cam.targetX - this.cam.x) * 0.08;
      this.cam.y += (this.cam.targetY - this.cam.y) * 0.08;
      this.cam.z += (this.cam.targetZ - this.cam.z) * 0.08;
      this.cam.rotX += (this.cam.targetRotX - this.cam.rotX) * 0.08;
      this.cam.rotY += (this.cam.targetRotY - this.cam.rotY) * 0.08;

      if (this.cam.autoRotate && !this.isDragging) {
        this.cam.targetRotY += 0.0008;
      }

      // Update coordinates HUD
      const coordsEl = document.getElementById('camCoords');
      if (coordsEl) {
        coordsEl.textContent = `X: ${this.cam.rotX.toFixed(2)} | Y: ${this.cam.rotY.toFixed(2)} | Z: ${Math.round(this.cam.z)}`;
      }

      // Clear Canvas
      this.ctx.fillStyle = '#010308';
      this.ctx.fillRect(0, 0, this.width, this.height);

      // 1. Draw Starfield Particles
      this.drawStarfield();

      // 2. Project Nodes
      const renderNodes = [];
      for (let i = 0; i < this.nodes.length; i++) {
        const n = this.nodes[i];
        if (!n.active) {
          n.projected = null;
          continue;
        }
        const proj = this.project(n.x, n.y, n.z);
        if (proj) {
          const r = Math.max(1.8, n.size * proj.scale * 1.8);
          n.projected = { sx: proj.sx, sy: proj.sy, r, scale: proj.scale, zDepth: proj.zDepth };
          renderNodes.push(n);
        } else {
          n.projected = null;
        }
      }

      // 3. Draw Connecting Links (with depth sorting & neural pulses)
      this.drawLinks();

      // 4. Sort Nodes by Depth (Painter's Algorithm)
      renderNodes.sort((a, b) => b.projected.zDepth - a.projected.zDepth);

      // 5. Draw 3D Volumetric Glowing Nodes
      this.drawNodes(renderNodes);

      // 6. Draw Prominent Hub Labels
      this.drawLabels(renderNodes);

      requestAnimationFrame(this.animate);
    }

    drawStarfield() {
      const ctx = this.ctx;
      for (let i = 0; i < this.stars.length; i++) {
        const s = this.stars[i];
        const proj = this.project(s.x, s.y, s.z);
        if (proj) {
          const alpha = s.alpha * Math.min(1, 1400 / proj.zDepth);
          ctx.fillStyle = `rgba(180, 220, 255, ${alpha.toFixed(2)})`;
          ctx.beginPath();
          ctx.arc(proj.sx, proj.sy, s.size * proj.scale * 1.2, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }

    drawLinks() {
      const ctx = this.ctx;

      for (let i = 0; i < this.links.length; i++) {
        const link = this.links[i];
        const p1 = link.source.projected;
        const p2 = link.target.projected;
        if (!p1 || !p2) continue;

        // Depth-based opacity
        const avgZ = (p1.zDepth + p2.zDepth) * 0.5;
        const distFade = Math.max(0.04, Math.min(0.45, 800 / avgZ * 0.35));

        const isHighlighted = (this.hoveredNode && (link.source === this.hoveredNode || link.target === this.hoveredNode)) ||
                              (this.selectedNode && (link.source === this.selectedNode || link.target === this.selectedNode));

        const strokeAlpha = isHighlighted ? 0.9 : distFade;
        const strokeColor = isHighlighted ? '#00f0ff' : 'rgba(0, 180, 255, ' + strokeAlpha + ')';

        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = isHighlighted ? 1.8 : Math.max(0.5, 0.9 * p1.scale);
        ctx.beginPath();
        ctx.moveTo(p1.sx, p1.sy);
        ctx.lineTo(p2.sx, p2.sy);
        ctx.stroke();

        // Animated Neural Data Pulses
        link.pulseOffset = (link.pulseOffset + link.pulseSpeed) % 1;
        const px = p1.sx + (p2.sx - p1.sx) * link.pulseOffset;
        const py = p1.sy + (p2.sy - p1.sy) * link.pulseOffset;

        ctx.fillStyle = isHighlighted ? '#ffffff' : '#00ffff';
        ctx.beginPath();
        ctx.arc(px, py, isHighlighted ? 2.5 : 1.2, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    drawNodes(renderNodes) {
      const ctx = this.ctx;

      for (let i = 0; i < renderNodes.length; i++) {
        const n = renderNodes[i];
        const p = n.projected;
        const catMeta = CATEGORIES[n.category] || CATEGORIES.Files;
        const isHovered = n === this.hoveredNode;
        const isSelected = n === this.selectedNode;

        const baseColor = catMeta.color;
        const r = isHovered ? p.r * 1.35 : (isSelected ? p.r * 1.25 : p.r);

        // 1. Outer Glow Bloom Ring
        const glowRadius = r * (n.isKeyHub ? 2.8 : 2.0);
        const glowGrad = ctx.createRadialGradient(p.sx, p.sy, r * 0.3, p.sx, p.sy, glowRadius);
        glowGrad.addColorStop(0, catMeta.glow);
        glowGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');

        ctx.fillStyle = glowGrad;
        ctx.beginPath();
        ctx.arc(p.sx, p.sy, glowRadius, 0, Math.PI * 2);
        ctx.fill();

        // 2. Volumetric 3D Sphere (Gradient with light offset)
        const lightX = p.sx - r * 0.35;
        const lightY = p.sy - r * 0.35;
        const sphereGrad = ctx.createRadialGradient(lightX, lightY, r * 0.1, p.sx, p.sy, r);
        sphereGrad.addColorStop(0, '#ffffff');
        sphereGrad.addColorStop(0.35, baseColor);
        sphereGrad.addColorStop(1, '#02050f');

        ctx.fillStyle = sphereGrad;
        ctx.beginPath();
        ctx.arc(p.sx, p.sy, r, 0, Math.PI * 2);
        ctx.fill();

        // 3. Selection / Hover Reticle
        if (isHovered || isSelected) {
          ctx.strokeStyle = '#00ffff';
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.arc(p.sx, p.sy, r + 4, 0, Math.PI * 2);
          ctx.stroke();

          // Corner tech ticks
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 1;
          const tr = r + 7;
          ctx.beginPath();
          ctx.moveTo(p.sx - tr, p.sy); ctx.lineTo(p.sx - tr + 3, p.sy);
          ctx.moveTo(p.sx + tr, p.sy); ctx.lineTo(p.sx + tr - 3, p.sy);
          ctx.moveTo(p.sx, p.sy - tr); ctx.lineTo(p.sx, p.sy - tr + 3);
          ctx.moveTo(p.sx, p.sy + tr); ctx.lineTo(p.sx, p.sy + tr - 3);
          ctx.stroke();
        }
      }
    }

    drawLabels(renderNodes) {
      const ctx = this.ctx;
      ctx.font = '10px "SF Mono", "JetBrains Mono", Consolas, monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      // Always draw labels for key hubs and hovered/selected nodes
      for (let i = 0; i < renderNodes.length; i++) {
        const n = renderNodes[i];
        const isProminent = n.isHub || n.isKeyHub || n.size > 14 || n === this.hoveredNode || n === this.selectedNode;

        if (isProminent && n.projected) {
          const p = n.projected;
          const labelY = p.sy + p.r + 10;
          const text = n.name;

          // Subtle text shadow box
          const textMetrics = ctx.measureText(text);
          const bgW = textMetrics.width + 8;
          const bgH = 14;

          ctx.fillStyle = 'rgba(2, 6, 16, 0.78)';
          ctx.fillRect(p.sx - bgW / 2, labelY - bgH / 2, bgW, bgH);
          ctx.strokeStyle = 'rgba(0, 240, 255, 0.25)';
          ctx.lineWidth = 0.8;
          ctx.strokeRect(p.sx - bgW / 2, labelY - bgH / 2, bgW, bgH);

          ctx.fillStyle = (n === this.hoveredNode || n === this.selectedNode) ? '#00ffff' : '#cbd5e1';
          ctx.fillText(text, p.sx, labelY);
        }
      }
    }
  }

  /* --------------------------------------------------------------------------
     J.A.R.V.I.S. VOICE ASSISTANT INTERFACE LOGIC
     -------------------------------------------------------------------------- */
  class JarvisVoiceAssistant {
    constructor(graph) {
      this.graph = graph;
      this.isListening = true;
      this.isRecording = false;
      this.activeModel = 'OPUS-4-8';

      this.recognition = null;
      this.initSpeechRecognition();
      this.initUI();
      this.initArcReactorGauge();
    }

    initArcReactorGauge() {
      const group = document.getElementById('arcTicksGroup');
      if (!group) return;

      // Generate 72 circular tick marks around the arc reactor
      const totalTicks = 72;
      const radius = 142;
      const cx = 160;
      const cy = 160;

      for (let i = 0; i < totalTicks; i++) {
        const angle = (i / totalTicks) * Math.PI * 2;
        const isAmberSector = (i >= 12 && i <= 24); // Right-bottom quadrant

        const x1 = cx + (radius - (i % 6 === 0 ? 9 : 5)) * Math.cos(angle);
        const y1 = cy + (radius - (i % 6 === 0 ? 9 : 5)) * Math.sin(angle);
        const x2 = cx + radius * Math.cos(angle);
        const y2 = cy + radius * Math.sin(angle);

        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', x1);
        line.setAttribute('y1', y1);
        line.setAttribute('x2', x2);
        line.setAttribute('y2', y2);
        line.setAttribute('stroke', isAmberSector ? '#ffb703' : 'rgba(0, 240, 255, 0.45)');
        line.setAttribute('stroke-width', i % 6 === 0 ? '2' : '1');
        if (isAmberSector) {
          line.setAttribute('filter', 'url(#goldGlow)');
        }
        group.appendChild(line);
      }
    }

    initSpeechRecognition() {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = 'ru-RU';

        this.recognition.onstart = () => {
          this.setRecordingState(true);
          SoundFX.beep(880, 0.08, 'sine', 0.1);
        };

        this.recognition.onresult = (event) => {
          let transcript = '';
          for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
          }
          const field = document.getElementById('jarvisInputField');
          if (field) field.value = transcript;

          if (event.results[0].isFinal) {
            this.handleCommand(transcript);
          }
        };

        this.recognition.onerror = () => {
          this.setRecordingState(false);
        };

        this.recognition.onend = () => {
          this.setRecordingState(false);
        };
      }
    }

    setRecordingState(isRec) {
      this.isRecording = isRec;
      const micBtn = document.getElementById('voiceMicBtn');
      const micLabel = document.getElementById('micBtnLabel');
      const waveRing = document.getElementById('audioReactiveWaveRing');

      if (micBtn) {
        if (isRec) micBtn.classList.add('recording');
        else micBtn.classList.remove('recording');
      }

      if (micLabel) {
        micLabel.textContent = isRec ? 'СЛУШАЮ ВАС, СЭР…' : 'УДЕРЖИВАЙТЕ ИЛИ НАЖМИТЕ ДЛЯ ГОЛОСА';
        micLabel.style.color = isRec ? '#ff3366' : 'var(--fg-mute)';
      }

      if (waveRing) {
        waveRing.setAttribute('stroke', isRec ? '#ff3366' : '#00ffff');
        waveRing.setAttribute('stroke-width', isRec ? '4' : '2');
      }
    }

    toggleVoice() {
      if (this.recognition) {
        if (this.isRecording) {
          this.recognition.stop();
        } else {
          try { this.recognition.start(); }
          catch (_) { this.simulateVoicePrompt(); }
        }
      } else {
        this.simulateVoicePrompt();
      }
    }

    simulateVoicePrompt() {
      const presets = [
        'Jarvis, scan knowledge graph',
        'Jarvis, focus AI Workshop',
        'Jarvis, show skills cluster',
        'Jarvis, isolate GEO Suite',
        'Jarvis, status report'
      ];
      const cmd = presets[Math.floor(Math.random() * presets.length)];
      const field = document.getElementById('jarvisInputField');
      if (field) field.value = cmd;
      this.handleCommand(cmd);
    }

    initUI() {
      // Clock
      const initTime = document.getElementById('initTime');
      if (initTime) {
        initTime.textContent = new Date().toLocaleTimeString();
      }

      // Mic Button
      const micBtn = document.getElementById('voiceMicBtn');
      if (micBtn) {
        micBtn.addEventListener('click', () => this.toggleVoice());
      }

      // Form submission
      const chatForm = document.getElementById('jarvisChatForm');
      const chatField = document.getElementById('jarvisInputField');
      if (chatForm && chatField) {
        chatForm.addEventListener('submit', (e) => {
          e.preventDefault();
          const text = chatField.value.trim();
          if (text) {
            chatField.value = '';
            this.handleCommand(text);
          }
        });
      }

      // Preset Chips
      document.querySelectorAll('.preset-chip').forEach(chip => {
        chip.addEventListener('click', () => {
          const cmd = chip.dataset.cmd;
          if (cmd) this.handleCommand(cmd);
          SoundFX.beep(720, 0.05, 'sine', 0.06);
        });
      });

      // Model Modal
      const modelBtn = document.getElementById('modelSelectBtn');
      const modelModal = document.getElementById('modelModal');
      const closeModelBtn = document.getElementById('closeModelModalBtn');

      if (modelBtn && modelModal) {
        modelBtn.addEventListener('click', () => {
          modelModal.style.display = 'grid';
          SoundFX.beep(600, 0.08, 'sine', 0.06);
        });
      }
      if (closeModelBtn && modelModal) {
        closeModelBtn.addEventListener('click', () => {
          modelModal.style.display = 'none';
        });
      }

      // Model Options Selection
      document.querySelectorAll('.model-option').forEach(opt => {
        opt.addEventListener('click', () => {
          const modelName = opt.dataset.model;
          if (modelName) {
            this.activeModel = modelName;
            document.querySelectorAll('.model-option').forEach(o => o.classList.remove('active'));
            opt.classList.add('active');
            const curEl = document.getElementById('currentModelName');
            if (curEl) curEl.textContent = modelName;
            if (modelModal) modelModal.style.display = 'none';
            this.addLogMsg('jarvis', `Модель переключена на: ${modelName}. Нейронные веса скомпилированы.`);
            SoundFX.chime([587, 740, 880]);
          }
        });
      });
    }

    async handleCommand(text) {
      this.addLogMsg('user', text);
      SoundFX.beep(550, 0.08, 'sine', 0.07);

      // Jarvis thinking bubble
      const typingBubble = this.addLogMsg('jarvis', 'Обработка директивы…', true);

      // Perform NLP / Voice command routing
      const reply = await this.routeDirective(text);

      typingBubble.classList.remove('typing');
      typingBubble.querySelector('.term-bubble').textContent = reply;

      // Speak reply using SpeechSynthesis if available
      this.speak(reply);
    }

    async routeDirective(cmd) {
      const lower = cmd.toLowerCase();

      if (lower.includes('scan') || lower.includes('сканир') || lower.includes('обзор')) {
        this.graph.cam.targetRotY += Math.PI * 0.7;
        this.graph.cam.targetZ = 850;
        return 'Сканирование квантового графа выполнено: 484 узла активны, 1,842 синаптических соединения синхронизированы без задержек.';
      }

      if (lower.includes('skill') || lower.includes('навык') || lower.includes('синий')) {
        this.graph.filterCategory('Skills');
        this.graph.cam.targetX = -220;
        this.graph.cam.targetY = 0;
        this.graph.cam.targetZ = 550;
        return 'Изолирован левый кластер Skills: 197 нейронных алгоритмов и процедур управления MARK L.';
      }

      if (lower.includes('workshop') || lower.includes('воркшоп')) {
        const workshop = this.graph.nodes.find(n => n.name === 'AI Workshop');
        if (workshop) this.graph.selectNode(workshop);
        return 'Центральный хаб AI Workshop зафиксирован в фокусе 3D-матрицы.';
      }

      if (lower.includes('geo') || lower.includes('гео')) {
        const geo = this.graph.nodes.find(n => n.name === 'GEO Suite' || n.name === 'GEO');
        if (geo) this.graph.selectNode(geo);
        return 'Комплекс GEO Suite активирован: геопространственная триангуляция и спутниковые координаты готовы.';
      }

      if (lower.includes('children') || lower.includes('book') || lower.includes('книг')) {
        const books = this.graph.nodes.find(n => n.name === 'AI Children’s Books');
        if (books) this.graph.selectNode(books);
        return 'Проект детских книг AI Children’s Books открыт. Модели генерации иллюстраций и текстовые ветви загружены.';
      }

      if (lower.includes('status') || lower.includes('отчет') || lower.includes('система')) {
        return `Статус системы: Ядро ${this.activeModel} функционирует штатно. Память: 1.4 GB / 484 узла. Задержка сети: 4.2 мс.`;
      }

      // Try server API command if available
      try {
        if (window.API && window.API.sendCommand) {
          const res = await window.API.sendCommand(cmd);
          if (res && res.reply) return res.reply;
        }
      } catch (_) {}

      return `Команда «${cmd}» принята и направлена в нейронный контур ${this.activeModel}.`;
    }

    speak(text) {
      if ('speechSynthesis' in window) {
        try {
          window.speechSynthesis.cancel();
          const utter = new SpeechSynthesisUtterance(text);
          utter.rate = 1.05;
          utter.pitch = 0.95;
          utter.lang = 'ru-RU';
          window.speechSynthesis.speak(utter);
        } catch (_) {}
      }
    }

    addLogMsg(sender, text, isTyping = false) {
      const feed = document.getElementById('jarvisLogFeed');
      if (!feed) return null;

      const timeStr = new Date().toLocaleTimeString();
      const div = document.createElement('div');
      div.className = `term-msg term-${sender}` + (isTyping ? ' typing' : '');
      div.innerHTML = `
        <div class="term-sender">
          <span class="sender-tag">${sender === 'jarvis' ? 'J.A.R.V.I.S.' : 'OPERATOR'}</span>
          <span class="term-time">${timeStr}</span>
        </div>
        <div class="term-bubble">${text}</div>
      `;
      feed.appendChild(div);
      feed.scrollTop = feed.scrollHeight;
      return div;
    }
  }

  /* --------------------------------------------------------------------------
     BOOTSTRAP EVERYTHING ON DOM READY
     -------------------------------------------------------------------------- */
  window.addEventListener('DOMContentLoaded', () => {
    // 1. Generate 484 Nodes Knowledge Graph
    const graphData = generateGraphData();

    // 2. Initialize 3D Engine
    const canvas = document.getElementById('graphCanvas');
    const graph = new KnowledgeGraph3D(canvas, graphData);

    // 3. Initialize J.A.R.V.I.S. Voice Assistant
    const assistant = new JarvisVoiceAssistant(graph);

    // 4. Header Actions & Search
    const searchInput = document.getElementById('nodeSearchInput');
    const clearSearch = document.getElementById('clearSearchBtn');

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        const val = e.target.value;
        graph.search(val);
        if (clearSearch) clearSearch.style.display = val ? 'block' : 'none';
      });
    }
    if (clearSearch && searchInput) {
      clearSearch.addEventListener('click', () => {
        searchInput.value = '';
        graph.search('');
        clearSearch.style.display = 'none';
        searchInput.focus();
      });
    }

    // Reset 3D Cam
    const resetCamBtn = document.getElementById('resetCamBtn');
    if (resetCamBtn) {
      resetCamBtn.addEventListener('click', () => graph.resetCamera());
    }

    // Auto-Rotate Toggle
    const autoRotBtn = document.getElementById('autoRotateToggle');
    if (autoRotBtn) {
      autoRotBtn.addEventListener('click', () => {
        graph.cam.autoRotate = !graph.cam.autoRotate;
        autoRotBtn.classList.toggle('hud-btn-accent', graph.cam.autoRotate);
        SoundFX.beep(600, 0.06, 'sine', 0.05);
      });
    }

    // Sound Toggle
    const soundBtn = document.getElementById('soundToggleBtn');
    if (soundBtn) {
      soundBtn.addEventListener('click', () => {
        const on = SoundFX.toggle();
        soundBtn.classList.toggle('hud-btn-accent', on);
        SoundFX.beep(on ? 880 : 330, 0.08, 'sine', 0.08);
      });
    }

    // Scanlines Toggle
    const scanBtn = document.getElementById('scanlineToggleBtn');
    const scanLayer = document.getElementById('scanlinesLayer');
    if (scanBtn && scanLayer) {
      scanBtn.addEventListener('click', () => {
        scanLayer.classList.toggle('off');
        scanBtn.classList.toggle('hud-btn-accent', !scanLayer.classList.contains('off'));
        SoundFX.beep(500, 0.05, 'square', 0.04);
      });
    }

    // Layout Switcher
    const layoutBtn = document.getElementById('toggleLayoutBtn');
    const layoutLbl = document.getElementById('layoutModeLabel');
    const layouts = ['Cosmic Galaxy', 'Neural Brain', 'Cluster Tree', 'Quantum Cloud'];
    let curLayoutIdx = 0;

    if (layoutBtn && layoutLbl) {
      layoutBtn.addEventListener('click', () => {
        curLayoutIdx = (curLayoutIdx + 1) % layouts.length;
        const name = layouts[curLayoutIdx];
        layoutLbl.textContent = name;
        graph.setLayoutMode(name.toLowerCase());
      });
    }

    // Legend Category Clicks
    document.querySelectorAll('.legend-item').forEach(item => {
      item.addEventListener('click', () => {
        const cat = item.dataset.cat;
        if (cat) {
          graph.filterCategory(cat);
          SoundFX.beep(750, 0.07, 'sine', 0.07);
        }
      });
    });

    const resetFiltersBtn = document.getElementById('resetFiltersBtn');
    if (resetFiltersBtn) {
      resetFiltersBtn.addEventListener('click', () => {
        graph.resetFilters();
        SoundFX.beep(500, 0.08, 'sine', 0.06);
      });
    }

    // Node Inspector Actions
    const closeInspectorBtn = document.getElementById('closeInspectorBtn');
    const inspectorDrawer = document.getElementById('nodeInspectorDrawer');
    if (closeInspectorBtn && inspectorDrawer) {
      closeInspectorBtn.addEventListener('click', () => {
        inspectorDrawer.classList.remove('open');
      });
    }

    const focusNodeBtn = document.getElementById('focusNodeBtn');
    if (focusNodeBtn) {
      focusNodeBtn.addEventListener('click', () => graph.focusActiveNode());
    }

    const askJarvisBtn = document.getElementById('askJarvisAboutNodeBtn');
    if (askJarvisBtn) {
      askJarvisBtn.addEventListener('click', () => {
        if (graph.selectedNode) {
          assistant.handleCommand(`Jarvis, tell me about ${graph.selectedNode.name}`);
        }
      });
    }

    // Mini D-Pad Controls
    const zIn = document.getElementById('zoomInBtn');
    const zOut = document.getElementById('zoomOutBtn');
    const tUp = document.getElementById('tiltUpBtn');
    const tDown = document.getElementById('tiltDownBtn');
    const rLeft = document.getElementById('rotLeftBtn');
    const rRight = document.getElementById('rotRightBtn');

    if (zIn) zIn.addEventListener('click', () => { graph.cam.targetZ = Math.max(220, graph.cam.z - 120); SoundFX.beep(800, 0.04); });
    if (zOut) zOut.addEventListener('click', () => { graph.cam.targetZ = Math.min(2400, graph.cam.z + 120); SoundFX.beep(700, 0.04); });
    if (tUp) tUp.addEventListener('click', () => { graph.cam.targetRotX -= 0.15; SoundFX.beep(600, 0.04); });
    if (tDown) tDown.addEventListener('click', () => { graph.cam.targetRotX += 0.15; SoundFX.beep(600, 0.04); });
    if (rLeft) rLeft.addEventListener('click', () => { graph.cam.targetRotY -= 0.25; SoundFX.beep(600, 0.04); });
    if (rRight) rRight.addEventListener('click', () => { graph.cam.targetRotY += 0.25; SoundFX.beep(600, 0.04); });

    // Initial Chime
    setTimeout(() => SoundFX.chime([523, 659, 783, 1046]), 400);
  });
})();
