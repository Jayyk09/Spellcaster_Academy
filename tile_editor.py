#!/usr/bin/env python3
"""
Tile Editor - Web-based visual editor for world_map.json.

Usage:
    python tile_editor.py              # Opens browser at http://localhost:8090
    python tile_editor.py --port 9000  # Use custom port

Opens a browser-based tile editor that lets you visually place and erase tiles
on the map grid, with actual tileset image previews.
"""

import argparse
import json
import os
import sys
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TILESETS_DIR = os.path.join(BASE_DIR, 'assets', 'sprites', 'tilesets')
MAP_PATH = os.path.join(BASE_DIR, 'data', 'world_map.json')

# Tileset config matching core/tilemap.py TileMap.load_tilesets()
TILESET_CONFIG = {
    'grass':    {'file': 'grass.png',        'tile_size': 16},
    'plains':   {'file': 'plains.png',       'tile_size': 16},
    'objects':  {'file': 'objects.png',       'tile_size': 16},
    'water':    {'file': 'water-sheet.png',   'tile_size': 16},
    'decor16':  {'file': 'decor_16x16.png',  'tile_size': 16},
    'decor8':   {'file': 'decor_8x8.png',    'tile_size':  8},
    'flooring': {'file': 'floors/flooring.png', 'tile_size': 16},
    'fences':   {'file': 'fences.png',       'tile_size': 16},
}

# Multi-tile region definitions from core/tileset.py
OBJECTS_REGIONS = {
    "0,5": [3, 4, 15, True],
    "3,5": [3, 4, 15, True],
    "0,9": [3, 4, 15, True],
    "3,9": [3, 4, 15, True],
    "6,7": [2, 2, 15, True],
    "6,5": [2, 1, 15, True],
    "6,6": [2, 1, 15, True],
    "6,9": [3, 1, 15, True],
    "8,6": [2, 3, 15, True],
    "10,7": [2, 2, 15, True],
    "0,0": [1, 1, 15, True],
    "0,1": [1, 1, 15, True],
    "1,1": [1, 1, 15, True],
    "2,1": [1, 1, 15, True],
    "6,0": [1, 1, 15, True],
    "8,0": [1, 1, 15, True],
    "8,1": [1, 1, 15, True],
}

FENCES_REGIONS = {
    "0,0": [1, 3, 15, False],
    "1,3": [3, 1, 15, False],
    "0,3": [1, 1, 15, False],
}


class TileEditorHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the tile editor."""

    def log_message(self, format, *args):
        """Suppress default logging for cleaner output."""
        pass

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_html(self, html):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())

    def _send_file(self, path, content_type):
        try:
            with open(path, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Cache-Control', 'max-age=3600')
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/':
            self._send_html(EDITOR_HTML)
        elif path == '/api/map':
            try:
                with open(MAP_PATH, 'r') as f:
                    data = json.load(f)
                self._send_json(data)
            except Exception as e:
                self._send_json({'error': str(e)}, 500)
        elif path == '/api/config':
            self._send_json({
                'tilesets': TILESET_CONFIG,
                'objects_regions': OBJECTS_REGIONS,
                'fences_regions': FENCES_REGIONS,
            })
        elif path.startswith('/tilesets/'):
            rel_path = path[len('/tilesets/'):]
            file_path = os.path.normpath(os.path.join(TILESETS_DIR, rel_path))
            # Security: ensure path is within tilesets directory
            if not file_path.startswith(os.path.normpath(TILESETS_DIR)):
                self.send_response(403)
                self.end_headers()
                return
            self._send_file(file_path, 'image/png')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/save':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                data = json.loads(body)
                with open(MAP_PATH, 'w') as f:
                    json.dump(data, f, indent=2)
                    f.write('\n')
                self._send_json({'ok': True})
                print(f"  Map saved to {MAP_PATH}")
            except Exception as e:
                self._send_json({'error': str(e)}, 500)
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


EDITOR_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Tile Editor - Spellcaster Academy</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #1a1a2e; color: #e0e0e0; font-family: 'Segoe UI', system-ui, sans-serif; overflow: hidden; height: 100vh; display: flex; flex-direction: column; }

/* Toolbar */
#toolbar { display: flex; align-items: center; gap: 8px; padding: 6px 12px; background: #16213e; border-bottom: 2px solid #0f3460; flex-shrink: 0; flex-wrap: wrap; }
#toolbar button { background: #0f3460; color: #e0e0e0; border: 1px solid #1a4a8a; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 13px; white-space: nowrap; }
#toolbar button:hover { background: #1a4a8a; }
#toolbar button.active { background: #e94560; border-color: #e94560; }
.toolbar-sep { width: 1px; height: 24px; background: #0f3460; margin: 0 4px; }
.toolbar-label { font-size: 12px; color: #888; margin-right: 2px; }
#brush-indicator { display: flex; align-items: center; gap: 6px; background: #0f3460; padding: 3px 10px; border-radius: 4px; font-size: 13px; }
#brush-preview { width: 24px; height: 24px; border: 1px solid #1a4a8a; background: #111; image-rendering: pixelated; }

/* Main area */
#main { display: flex; flex: 1; overflow: hidden; }

/* Canvas */
#canvas-wrap { flex: 1; position: relative; overflow: hidden; cursor: crosshair; }
#canvas-wrap canvas { position: absolute; top: 0; left: 0; image-rendering: pixelated; }

/* Palette sidebar */
#palette { width: 260px; background: #16213e; border-left: 2px solid #0f3460; display: flex; flex-direction: column; flex-shrink: 0; }
#palette-search { padding: 6px; border-bottom: 1px solid #0f3460; }
#palette-search input { width: 100%; padding: 5px 8px; background: #0d1b3e; border: 1px solid #1a4a8a; color: #e0e0e0; border-radius: 3px; font-size: 13px; }
#palette-list { flex: 1; overflow-y: auto; padding: 4px; }
.palette-group { margin-bottom: 8px; }
.palette-group-title { font-size: 11px; color: #888; padding: 4px 6px; text-transform: uppercase; letter-spacing: 1px; }
.palette-item { display: flex; align-items: center; gap: 8px; padding: 4px 6px; border-radius: 3px; cursor: pointer; font-size: 13px; }
.palette-item:hover { background: #1a3a6a; }
.palette-item.selected { background: #e94560; color: #fff; }
.palette-tile { width: 32px; height: 32px; border: 1px solid #333; image-rendering: pixelated; flex-shrink: 0; background: #111; }
.palette-alias { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.palette-info { font-size: 10px; color: #666; }

/* Status bar */
#statusbar { display: flex; gap: 16px; padding: 3px 12px; background: #0f3460; font-size: 12px; color: #888; flex-shrink: 0; }
#statusbar span { white-space: nowrap; }

/* Scrollbar styling */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #0d1b3e; }
::-webkit-scrollbar-thumb { background: #1a4a8a; border-radius: 4px; }
</style>
</head>
<body>

<div id="toolbar">
  <span class="toolbar-label">Layer:</span>
  <button class="layer-btn active" data-layer="ground">1 Ground</button>
  <button class="layer-btn" data-layer="decorations">2 Decor</button>
  <button class="layer-btn" data-layer="objects">3 Objects</button>
  <button class="layer-btn" data-layer="ysort">4 YSort</button>
  <div class="toolbar-sep"></div>
  <div id="brush-indicator">
    <canvas id="brush-preview" width="24" height="24"></canvas>
    <span id="brush-name">Eraser (.)</span>
  </div>
  <div class="toolbar-sep"></div>
  <button id="btn-eraser" title="Eraser (E)">Eraser</button>
  <button id="btn-undo" title="Undo (Ctrl+Z)">Undo</button>
  <div class="toolbar-sep"></div>
  <button id="btn-save" title="Save (Ctrl+S)">Save</button>
  <button id="btn-export" title="Export JSON">Export</button>
  <div class="toolbar-sep"></div>
  <button id="btn-zoom-in" title="Zoom In (+)">+</button>
  <button id="btn-zoom-out" title="Zoom Out (-)">-</button>
  <button id="btn-zoom-fit" title="Fit to window">Fit</button>
  <div class="toolbar-sep"></div>
  <button id="btn-grid" class="active" title="Toggle Grid (G)">Grid</button>
</div>

<div id="main">
  <div id="canvas-wrap">
    <canvas id="editor-canvas"></canvas>
  </div>
  <div id="palette">
    <div id="palette-search"><input type="text" placeholder="Search tiles..." id="search-input"></div>
    <div id="palette-list"></div>
  </div>
</div>

<div id="statusbar">
  <span id="status-pos">Pos: -</span>
  <span id="status-cell">Cell: -</span>
  <span id="status-zoom">Zoom: 3x</span>
  <span id="status-layer">Layer: ground</span>
  <span id="status-msg"></span>
</div>

<script>
// ─── State ───
let mapData = null;
let config = null;
let tileImages = {};  // tileset_name -> Image
let currentLayer = 'ground';
let selectedBrush = null;  // null = eraser, or {alias, tileset, col, row}
let zoom = 3;
let panX = 0, panY = 0;
let isPanning = false;
let panStart = {x:0, y:0, px:0, py:0};
let isDrawing = false;
let drawButton = -1;
let showGrid = true;
let undoStack = [];
let currentStroke = null;  // accumulated changes for current mouse drag
const MAX_UNDO = 100;
const TILE_SIZE = 16;
let layerCanvases = {};
let layerNeedsRedraw = {};
let regionLookup = new Map();

const canvas = document.getElementById('editor-canvas');
const ctx = canvas.getContext('2d');
const wrap = document.getElementById('canvas-wrap');

// ─── Init ───
async function init() {
  const [mapResp, cfgResp] = await Promise.all([
    fetch('/api/map').then(r => r.json()),
    fetch('/api/config').then(r => r.json())
  ]);
  mapData = mapResp;
  config = cfgResp;

  // Build region lookup map (using Map for reliable key matching)
  regionLookup.clear();
  if (config.objects_regions) {
    for (const [key, val] of Object.entries(config.objects_regions)) {
      const parts = key.split(',');
      const c = parseInt(parts[0], 10);
      const r = parseInt(parts[1], 10);
      regionLookup.set('objects:' + c + ',' + r, val);
    }
  }
  if (config.fences_regions) {
    for (const [key, val] of Object.entries(config.fences_regions)) {
      const parts = key.split(',');
      const c = parseInt(parts[0], 10);
      const r = parseInt(parts[1], 10);
      regionLookup.set('fences:' + c + ',' + r, val);
    }
  }
  console.log('[TileEditor] Built region lookup with', regionLookup.size, 'entries');

  // Load tileset images
  const promises = [];
  for (const [name, info] of Object.entries(config.tilesets)) {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    promises.push(new Promise((resolve) => {
      img.onload = () => { tileImages[name] = img; resolve(); };
      img.onerror = () => resolve();
      img.src = '/tilesets/' + info.file;
    }));
  }
  await Promise.all(promises);

  buildPalette();

  // Debug: verify region lookup works
  const _testRegion = getRegionInfo('objects', 0, 5);
  console.log('[TileEditor] Test region lookup objects(0,5):', _testRegion);

  initLayerCanvases();
  resizeCanvas();
  fitToWindow();
  render();

  window.addEventListener('resize', () => { resizeCanvas(); render(); });
  setupCanvasEvents();
  setupToolbarEvents();
  setupKeyboard();
}

// ─── Canvas sizing ───
function resizeCanvas() {
  canvas.width = wrap.clientWidth;
  canvas.height = wrap.clientHeight;
}

function fitToWindow() {
  if (!mapData) return;
  const mapW = mapData.width * TILE_SIZE;
  const mapH = mapData.height * TILE_SIZE;
  const scaleX = (wrap.clientWidth - 40) / mapW;
  const scaleY = (wrap.clientHeight - 40) / mapH;
  zoom = Math.max(1, Math.floor(Math.min(scaleX, scaleY)));
  panX = (wrap.clientWidth - mapW * zoom) / 2;
  panY = (wrap.clientHeight - mapH * zoom) / 2;
  updateStatusZoom();
}

// ─── Grid parsing helpers ───
function getGrid(layerName) {
  if (!mapData || !mapData.layers || !mapData.layers[layerName]) return null;
  return mapData.layers[layerName].grid;
}

function parseRow(rowStr) {
  return rowStr.split(/\s+/).filter(s => s.length > 0);
}

function getCellAlias(layerName, x, y) {
  const grid = getGrid(layerName);
  if (!grid || y >= grid.length) return '.';
  const tiles = parseRow(grid[y]);
  if (x >= tiles.length) return '.';
  return tiles[x];
}

function setCellAlias(layerName, x, y, alias) {
  const grid = getGrid(layerName);
  if (!grid || y >= grid.length) return;
  const tiles = parseRow(grid[y]);
  while (tiles.length <= x) tiles.push('.');
  tiles[x] = alias;
  // Rebuild row string: each alias left-padded to 4 chars
  let row = tiles.map(a => a.padStart(4)).join('');
  // Trim trailing whitespace
  row = row.replace(/\s+$/, '');
  grid[y] = row;
  layerNeedsRedraw[layerName] = true;
}

// ─── Tile lookup ───
function getTileDef(alias) {
  if (!mapData || !mapData.tile_defs) return null;
  const def = mapData.tile_defs[alias];
  if (!def || !Array.isArray(def)) return null;
  return {tileset: def[0], col: def[1], row: def[2]};
}

function getRegionInfo(tilesetName, col, row) {
  if (tilesetName !== 'objects' && tilesetName !== 'fences') return null;
  const key = tilesetName + ':' + col + ',' + row;
  return regionLookup.get(key) || null;  // [w, h, ysort, collision]
}

// ─── Rendering (offscreen canvas approach) ───
// Each layer is rendered at 1:1 pixel scale to an offscreen canvas,
// then the offscreen canvas is drawn to the display canvas with zoom.
// This eliminates per-tile scaling artifacts with multi-row source rects.

function initLayerCanvases() {
  const w = mapData.width * TILE_SIZE;
  const h = mapData.height * TILE_SIZE;
  for (const name of ['ground', 'decorations', 'objects', 'ysort']) {
    const cvs = document.createElement('canvas');
    cvs.width = w;
    cvs.height = h;
    layerCanvases[name] = cvs;
    layerNeedsRedraw[name] = true;
  }
}

function redrawLayer(layerName) {
  const cvs = layerCanvases[layerName];
  if (!cvs) return;
  const lctx = cvs.getContext('2d');
  lctx.clearRect(0, 0, cvs.width, cvs.height);
  lctx.imageSmoothingEnabled = false;

  const grid = getGrid(layerName);
  if (!grid) return;

  // Two-pass rendering: single tiles first, then multi-tile regions on top.
  // This prevents adjacent single tiles from overwriting multi-tile sprites.
  const multiTiles = [];

  // Pass 1: single tiles
  for (let y = 0; y < grid.length; y++) {
    const tiles = parseRow(grid[y]);
    for (let x = 0; x < tiles.length; x++) {
      const alias = tiles[x];
      if (alias === '.' || alias === '_' || alias === 'null') continue;

      const def = getTileDef(alias);
      if (!def) continue;

      const img = tileImages[def.tileset];
      if (!img) continue;

      const ts = config.tilesets[def.tileset];
      if (!ts) continue;
      const tileSize = ts.tile_size;

      const region = getRegionInfo(def.tileset, def.col, def.row);
      if (region && (region[0] > 1 || region[1] > 1)) {
        // Defer multi-tile regions to pass 2
        multiTiles.push({x, y, def, img, tileSize, region});
        continue;
      }

      if (region) {
        // 1x1 region, draw normally
        lctx.drawImage(img,
          def.col * tileSize, def.row * tileSize,
          tileSize, tileSize,
          x * TILE_SIZE, y * TILE_SIZE,
          TILE_SIZE, TILE_SIZE
        );
      } else if (tileSize === 8) {
        lctx.drawImage(img,
          def.col * tileSize, def.row * tileSize,
          tileSize, tileSize,
          x * TILE_SIZE, y * TILE_SIZE,
          tileSize, tileSize
        );
      } else {
        lctx.drawImage(img,
          def.col * tileSize, def.row * tileSize,
          tileSize, tileSize,
          x * TILE_SIZE, y * TILE_SIZE,
          TILE_SIZE, TILE_SIZE
        );
      }
    }
  }

  // Pass 2: multi-tile regions drawn on top
  for (const mt of multiTiles) {
    const [rw, rh] = mt.region;
    lctx.drawImage(mt.img,
      mt.def.col * mt.tileSize, mt.def.row * mt.tileSize,
      rw * mt.tileSize, rh * mt.tileSize,
      mt.x * TILE_SIZE, mt.y * TILE_SIZE,
      rw * TILE_SIZE, rh * TILE_SIZE
    );
  }

  layerNeedsRedraw[layerName] = false;
}

function render() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#111122';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  if (!mapData) return;

  // Redraw any dirty layer offscreen canvases at 1:1 scale
  for (const name of ['ground', 'decorations', 'objects', 'ysort']) {
    if (layerNeedsRedraw[name]) redrawLayer(name);
  }

  ctx.save();
  ctx.translate(panX, panY);
  ctx.scale(zoom, zoom);
  ctx.imageSmoothingEnabled = false;

  const w = mapData.width;
  const h = mapData.height;

  // Draw map background
  ctx.fillStyle = '#1a2a1a';
  ctx.fillRect(0, 0, w * TILE_SIZE, h * TILE_SIZE);

  // Composite pre-rendered layer canvases
  const layerOrder = ['ground', 'decorations', 'objects', 'ysort'];
  for (const layerName of layerOrder) {
    ctx.globalAlpha = layerName === currentLayer ? 1.0 : 0.4;
    ctx.drawImage(layerCanvases[layerName], 0, 0);
  }
  ctx.globalAlpha = 1.0;

  // Draw grid
  if (showGrid) {
    ctx.strokeStyle = 'rgba(255,255,255,0.12)';
    ctx.lineWidth = 1 / zoom;
    for (let x = 0; x <= w; x++) {
      ctx.beginPath();
      ctx.moveTo(x * TILE_SIZE, 0);
      ctx.lineTo(x * TILE_SIZE, h * TILE_SIZE);
      ctx.stroke();
    }
    for (let y = 0; y <= h; y++) {
      ctx.beginPath();
      ctx.moveTo(0, y * TILE_SIZE);
      ctx.lineTo(w * TILE_SIZE, y * TILE_SIZE);
      ctx.stroke();
    }
  }

  ctx.restore();
}

// ─── Palette ───
function buildPalette() {
  const list = document.getElementById('palette-list');
  list.innerHTML = '';
  if (!mapData || !mapData.tile_defs) return;

  // Group tile defs by category (using _comment keys)
  const groups = [];
  let currentGroup = {title: 'General', items: []};

  const entries = Object.entries(mapData.tile_defs);
  for (const [key, val] of entries) {
    if (key.startsWith('_')) {
      // Category comment
      if (currentGroup.items.length > 0) groups.push(currentGroup);
      currentGroup = {title: String(val), items: []};
      continue;
    }
    currentGroup.items.push({alias: key, def: val});
  }
  if (currentGroup.items.length > 0) groups.push(currentGroup);

  for (const group of groups) {
    const div = document.createElement('div');
    div.className = 'palette-group';
    div.innerHTML = `<div class="palette-group-title">${group.title}</div>`;

    for (const item of group.items) {
      const el = document.createElement('div');
      el.className = 'palette-item';
      el.dataset.alias = item.alias;

      const tileCanvas = document.createElement('canvas');
      tileCanvas.width = 32;
      tileCanvas.height = 32;
      tileCanvas.className = 'palette-tile';
      drawTilePreview(tileCanvas, item.def[0], item.def[1], item.def[2]);

      const nameSpan = document.createElement('span');
      nameSpan.className = 'palette-alias';
      nameSpan.textContent = item.alias;

      const infoSpan = document.createElement('span');
      infoSpan.className = 'palette-info';
      infoSpan.textContent = `${item.def[0]}[${item.def[1]},${item.def[2]}]`;

      el.appendChild(tileCanvas);
      el.appendChild(nameSpan);
      el.appendChild(infoSpan);

      el.addEventListener('click', () => selectBrush(item.alias));
      div.appendChild(el);
    }
    list.appendChild(div);
  }
}

function drawTilePreview(cvs, tilesetName, col, row) {
  const pctx = cvs.getContext('2d');
  pctx.imageSmoothingEnabled = false;
  pctx.fillStyle = '#111';
  pctx.fillRect(0, 0, 32, 32);

  const img = tileImages[tilesetName];
  if (!img) return;

  const ts = config.tilesets[tilesetName];
  if (!ts) return;
  const tileSize = ts.tile_size;

  const region = getRegionInfo(tilesetName, col, row);
  if (region) {
    const [rw, rh] = region;
    const srcW = rw * tileSize;
    const srcH = rh * tileSize;
    const scale = Math.min(32 / srcW, 32 / srcH);
    const dw = srcW * scale;
    const dh = srcH * scale;
    pctx.drawImage(img, col * tileSize, row * tileSize, srcW, srcH,
      (32 - dw) / 2, (32 - dh) / 2, dw, dh);
  } else {
    const scale = Math.min(32 / tileSize, 32 / tileSize);
    const dw = tileSize * scale;
    const dh = tileSize * scale;
    pctx.drawImage(img, col * tileSize, row * tileSize, tileSize, tileSize,
      (32 - dw) / 2, (32 - dh) / 2, dw, dh);
  }
}

function selectBrush(alias) {
  if (alias === null) {
    // Eraser
    selectedBrush = null;
    document.getElementById('brush-name').textContent = 'Eraser (.)';
    const bctx = document.getElementById('brush-preview').getContext('2d');
    bctx.clearRect(0, 0, 24, 24);
    bctx.fillStyle = '#333';
    bctx.fillRect(0, 0, 24, 24);
    bctx.strokeStyle = '#e94560';
    bctx.lineWidth = 2;
    bctx.beginPath(); bctx.moveTo(4, 4); bctx.lineTo(20, 20); bctx.stroke();
    bctx.beginPath(); bctx.moveTo(20, 4); bctx.lineTo(4, 20); bctx.stroke();
  } else {
    const def = getTileDef(alias);
    if (!def) return;
    selectedBrush = {alias, ...def};
    document.getElementById('brush-name').textContent = alias;

    const bCanvas = document.getElementById('brush-preview');
    const bctx = bCanvas.getContext('2d');
    bctx.imageSmoothingEnabled = false;
    bctx.clearRect(0, 0, 24, 24);

    const img = tileImages[def.tileset];
    const ts = config.tilesets[def.tileset];
    if (img && ts) {
      const tileSize = ts.tile_size;
      const region = getRegionInfo(def.tileset, def.col, def.row);
      if (region) {
        const [rw, rh] = region;
        const srcW = rw * tileSize;
        const srcH = rh * tileSize;
        const scale = Math.min(24 / srcW, 24 / srcH);
        bctx.drawImage(img, def.col * tileSize, def.row * tileSize, srcW, srcH,
          (24 - srcW * scale) / 2, (24 - srcH * scale) / 2, srcW * scale, srcH * scale);
      } else {
        bctx.drawImage(img, def.col * tileSize, def.row * tileSize, tileSize, tileSize, 0, 0, 24, 24);
      }
    }
  }

  // Update palette selection UI
  document.querySelectorAll('.palette-item').forEach(el => {
    el.classList.toggle('selected', alias !== null && el.dataset.alias === alias);
  });

  // Update eraser button
  document.getElementById('btn-eraser').classList.toggle('active', alias === null);
}

// ─── Search ───
document.getElementById('search-input').addEventListener('input', (e) => {
  const query = e.target.value.toLowerCase();
  document.querySelectorAll('.palette-group').forEach(group => {
    let anyVisible = false;
    group.querySelectorAll('.palette-item').forEach(item => {
      const visible = item.dataset.alias.toLowerCase().includes(query) ||
                      item.querySelector('.palette-info').textContent.toLowerCase().includes(query);
      item.style.display = visible ? '' : 'none';
      if (visible) anyVisible = true;
    });
    group.style.display = anyVisible ? '' : 'none';
  });
});

// ─── Canvas events ───
function screenToGrid(sx, sy) {
  const rect = canvas.getBoundingClientRect();
  const cx = sx - rect.left;
  const cy = sy - rect.top;
  const wx = (cx - panX) / zoom;
  const wy = (cy - panY) / zoom;
  const gx = Math.floor(wx / TILE_SIZE);
  const gy = Math.floor(wy / TILE_SIZE);
  return {gx, gy};
}

function isInBounds(gx, gy) {
  return mapData && gx >= 0 && gy >= 0 && gx < mapData.width && gy < mapData.height;
}

function setupCanvasEvents() {
  canvas.addEventListener('mousedown', (e) => {
    e.preventDefault();
    if (e.button === 1 || (e.button === 0 && e.getModifierState('Space'))) {
      // Pan
      isPanning = true;
      panStart = {x: e.clientX, y: e.clientY, px: panX, py: panY};
      canvas.style.cursor = 'grabbing';
      return;
    }
    if (e.button === 0 || e.button === 2) {
      isDrawing = true;
      drawButton = e.button;
      currentStroke = [];
      paintAt(e);
    }
  });

  canvas.addEventListener('mousemove', (e) => {
    if (isPanning) {
      panX = panStart.px + (e.clientX - panStart.x);
      panY = panStart.py + (e.clientY - panStart.y);
      render();
      return;
    }
    if (isDrawing) {
      paintAt(e);
    }
    // Update status
    const {gx, gy} = screenToGrid(e.clientX, e.clientY);
    if (isInBounds(gx, gy)) {
      document.getElementById('status-pos').textContent = `Pos: ${gx}, ${gy}`;
      const alias = getCellAlias(currentLayer, gx, gy);
      document.getElementById('status-cell').textContent = `Cell: ${alias}`;
    } else {
      document.getElementById('status-pos').textContent = 'Pos: -';
      document.getElementById('status-cell').textContent = 'Cell: -';
    }
  });

  canvas.addEventListener('mouseup', (e) => {
    if (isPanning) {
      isPanning = false;
      canvas.style.cursor = 'crosshair';
      return;
    }
    if (isDrawing) {
      isDrawing = false;
      drawButton = -1;
      if (currentStroke && currentStroke.length > 0) {
        undoStack.push({layer: currentLayer, changes: currentStroke});
        if (undoStack.length > MAX_UNDO) undoStack.shift();
      }
      currentStroke = null;
    }
  });

  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    const oldZoom = zoom;
    if (e.deltaY < 0) zoom = Math.min(20, zoom + 1);
    else zoom = Math.max(1, zoom - 1);

    // Zoom towards mouse
    panX = mx - (mx - panX) * (zoom / oldZoom);
    panY = my - (my - panY) * (zoom / oldZoom);

    updateStatusZoom();
    render();
  }, {passive: false});

  canvas.addEventListener('contextmenu', (e) => e.preventDefault());

  // Track space key for pan mode
  let spaceDown = false;
  document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && !spaceDown) {
      spaceDown = true;
      canvas.style.cursor = 'grab';
    }
  });
  document.addEventListener('keyup', (e) => {
    if (e.code === 'Space') {
      spaceDown = false;
      if (!isPanning) canvas.style.cursor = 'crosshair';
    }
  });
}

function paintAt(e) {
  const {gx, gy} = screenToGrid(e.clientX, e.clientY);
  if (!isInBounds(gx, gy)) return;

  const oldAlias = getCellAlias(currentLayer, gx, gy);
  let newAlias;

  if (drawButton === 2) {
    // Right-click = erase
    newAlias = '.';
  } else if (selectedBrush === null) {
    // Eraser selected
    newAlias = '.';
  } else {
    newAlias = selectedBrush.alias;
  }

  if (oldAlias === newAlias) return;

  // Check if this cell was already modified in this stroke
  if (currentStroke) {
    const existing = currentStroke.find(c => c.x === gx && c.y === gy);
    if (existing) return;  // Already modified in this stroke
  }

  setCellAlias(currentLayer, gx, gy, newAlias);
  if (currentStroke) {
    currentStroke.push({x: gx, y: gy, old: oldAlias, new: newAlias});
  }
  render();
}

// ─── Undo ───
function undo() {
  if (undoStack.length === 0) return;
  const action = undoStack.pop();
  for (const change of action.changes.reverse()) {
    setCellAlias(action.layer, change.x, change.y, change.old);
  }
  render();
  showStatus('Undo');
}

// ─── Save ───
async function saveMap() {
  try {
    const resp = await fetch('/api/save', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(mapData),
    });
    const result = await resp.json();
    if (result.ok) {
      showStatus('Saved!');
    } else {
      showStatus('Save failed: ' + (result.error || 'unknown'));
    }
  } catch (e) {
    showStatus('Save error: ' + e.message);
  }
}

function exportJSON() {
  const blob = new Blob([JSON.stringify(mapData, null, 2) + '\n'], {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'world_map.json';
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 5000);
  showStatus('Exported!');
}

// ─── Toolbar ───
function setupToolbarEvents() {
  // Layer buttons
  document.querySelectorAll('.layer-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      currentLayer = btn.dataset.layer;
      document.querySelectorAll('.layer-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('status-layer').textContent = 'Layer: ' + currentLayer;
      render();
    });
  });

  document.getElementById('btn-eraser').addEventListener('click', () => selectBrush(null));
  document.getElementById('btn-undo').addEventListener('click', undo);
  document.getElementById('btn-save').addEventListener('click', saveMap);
  document.getElementById('btn-export').addEventListener('click', exportJSON);
  document.getElementById('btn-zoom-in').addEventListener('click', () => {
    zoom = Math.min(20, zoom + 1);
    updateStatusZoom();
    render();
  });
  document.getElementById('btn-zoom-out').addEventListener('click', () => {
    zoom = Math.max(1, zoom - 1);
    updateStatusZoom();
    render();
  });
  document.getElementById('btn-zoom-fit').addEventListener('click', () => {
    fitToWindow();
    render();
  });
  document.getElementById('btn-grid').addEventListener('click', (e) => {
    showGrid = !showGrid;
    e.currentTarget.classList.toggle('active', showGrid);
    render();
  });

  // Initialize eraser as default
  selectBrush(null);
}

// ─── Keyboard ───
function setupKeyboard() {
  document.addEventListener('keydown', (e) => {
    // Don't capture when typing in search
    if (e.target.tagName === 'INPUT') return;

    if (e.ctrlKey || e.metaKey) {
      if (e.key === 'z') { e.preventDefault(); undo(); }
      else if (e.key === 's') { e.preventDefault(); saveMap(); }
      return;
    }

    switch (e.key) {
      case '1': document.querySelector('[data-layer="ground"]').click(); break;
      case '2': document.querySelector('[data-layer="decorations"]').click(); break;
      case '3': document.querySelector('[data-layer="objects"]').click(); break;
      case '4': document.querySelector('[data-layer="ysort"]').click(); break;
      case 'e': case 'E': selectBrush(null); break;
      case 'g': case 'G':
        document.getElementById('btn-grid').click();
        break;
      case '+': case '=':
        zoom = Math.min(20, zoom + 1);
        updateStatusZoom();
        render();
        break;
      case '-':
        zoom = Math.max(1, zoom - 1);
        updateStatusZoom();
        render();
        break;
    }
  });
}

// ─── Helpers ───
function updateStatusZoom() {
  document.getElementById('status-zoom').textContent = `Zoom: ${zoom}x`;
}

function showStatus(msg) {
  const el = document.getElementById('status-msg');
  el.textContent = msg;
  setTimeout(() => { if (el.textContent === msg) el.textContent = ''; }, 2000);
}

// ─── Start ───
init();
</script>
</body>
</html>
'''


def main():
    parser = argparse.ArgumentParser(description='Tile Editor for Spellcaster Academy')
    parser.add_argument('-p', '--port', type=int, default=8090, help='Server port (default: 8090)')
    parser.add_argument('--no-browser', action='store_true', help='Don\'t auto-open browser')
    args = parser.parse_args()

    server = HTTPServer(('127.0.0.1', args.port), TileEditorHandler)
    url = f'http://localhost:{args.port}'
    print(f'Tile Editor running at {url}')
    print('Press Ctrl+C to stop')

    if not args.no_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down.')
        server.server_close()


if __name__ == '__main__':
    main()
