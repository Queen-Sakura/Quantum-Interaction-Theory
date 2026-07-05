#!/usr/bin/env node
/**
 * 魔都三件套（+1）MCP Server
 *
 * 在对话中实时更新四座 HTML 建筑的内容。
 * 只记录最精华的进展——每一条更新都应是经过审计的增量。
 *
 * 三件套 + 东方明珠：
 * - 物理大厦（方形·联合国）
 * - 物理计算机大厦（方形·工程学）
 * - 数学大厦（方形·形式系统）
 * - 哲学塔（圆形·自指环·东方明珠·光速自信灯）
 */

const { Server } = require("@modelcontextprotocol/sdk/server/index.js");
const { StdioServerTransport } = require("@modelcontextprotocol/sdk/server/stdio.js");
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require("@modelcontextprotocol/sdk/types.js");
const fs = require("fs");
const path = require("path");

// ============================================================
// Config
// ============================================================
const BUILDINGS_DIR = path.resolve(__dirname, "..");
const BUILDINGS = {
  physics: {
    file: path.join(BUILDINGS_DIR, "物理大厦.html"),
    name: "物理大厦",
    description: "膜框架 · Q · EM统一 · 废弃清单",
  },
  computer: {
    file: path.join(BUILDINGS_DIR, "物理计算机大厦.html"),
    name: "物理计算机大厦",
    description: "四定律 · 全栈审计 · 内核全链路",
  },
  math: {
    file: path.join(BUILDINGS_DIR, "数学大厦.html"),
    name: "数学大厦",
    description: "三进制 · 哥德尔 · 相数 · 数学=膜的语法",
  },
  philosophy: {
    file: path.join(BUILDINGS_DIR, "哲学塔.html"),
    name: "哲学塔 · 东方明珠",
    description: "自指环 · 本体论 · 光速自信灯 · 方与圆",
  },
};

// ============================================================
// HTML helpers
// ============================================================
function readHTML(building) {
  return fs.readFileSync(BUILDINGS[building].file, "utf-8");
}

function writeHTML(building, html) {
  fs.writeFileSync(BUILDINGS[building].file, html, "utf-8");
}

/** Parse a building HTML into sections */
function parseFloors(html) {
  const floors = [];
  // Match floor blocks: <!-- ====== ... ====== --> ... floor-header ... floor-body
  const floorRegex = /<!--\s*=+\s*(\d+F|穹顶|地基)[^=]*=+\s*-->\s*\n\s*<div class="floor">\s*\n\s*<div class="floor-header">\s*\n\s*<span>([^<]*)<\/span>\s*\n\s*<span class="floor-num">([^<]*)<\/span>/gs;
  let match;
  while ((match = floorRegex.exec(html)) !== null) {
    floors.push({
      id: match[1],
      title: match[2].trim(),
      num: match[3].trim(),
      fullMatch: match[0],
      index: match.index,
    });
  }
  return floors;
}

/** Find the last floor block end index (before footer) */
function findInsertionPoint(html) {
  // Find the footer
  const footerMatch = html.match(/<div class="footer">/);
  if (footerMatch) {
    return footerMatch.index;
  }
  // Fallback: before closing skyline div (before last </div></body>)
  const skylineEnd = html.lastIndexOf('</div>\n</body>');
  if (skylineEnd !== -1) {
    return skylineEnd;
  }
  // Last resort: before </body>
  return html.lastIndexOf('</body>');
}

/** Generate a floor number string */
function nextFloorNum(html) {
  const floors = parseFloors(html);
  const nums = floors.map(f => f.num).filter(n => n.endsWith('F')).map(n => parseInt(n)).filter(n => !isNaN(n));
  if (nums.length === 0) return "1F";
  return (Math.max(...nums) + 1) + "F";
}

/** Build a new floor HTML block */
function buildFloor(num, title, bodyHTML, accent = "var(--accent)") {
  return `
<!-- ====== ${num} ====== -->
<div class="floor">
  <div class="floor-header">
    <span>${title}</span>
    <span class="floor-num">${num}</span>
  </div>
  <div class="floor-body">
    ${bodyHTML}
  </div>
</div>

`;
}

// ============================================================
// Tools
// ============================================================

/**
 * 魔都_add_finding
 * Add a new floor/section to a building.
 */
async function addFinding(args) {
  const { building, title, content } = args;
  if (!BUILDINGS[building]) {
    return { error: `Unknown building: ${building}. Use: physics, computer, math, philosophy` };
  }
  if (!title || !content) {
    return { error: "title and content are required" };
  }

  let html = readHTML(building);
  const insertAt = findInsertionPoint(html);
  const num = nextFloorNum(html);
  const floorHTML = buildFloor(num, title, content);

  html = html.slice(0, insertAt) + floorHTML + html.slice(insertAt);
  writeHTML(building, html);

  return {
    building: BUILDINGS[building].name,
    floor: num,
    title,
    message: `已添加到 ${BUILDINGS[building].name} · ${num} · "${title}"`,
  };
}

/**
 * 魔都_update_floor
 * Update an existing floor's body content.
 */
async function updateFloor(args) {
  const { building, floor_id, content } = args;
  if (!BUILDINGS[building]) {
    return { error: `Unknown building: ${building}. Use: physics, computer, math, philosophy` };
  }
  if (!floor_id || !content) {
    return { error: "floor_id and content are required" };
  }

  let html = readHTML(building);
  const floors = parseFloors(html);
  const target = floors.find(f => f.id === floor_id || f.num === floor_id);
  if (!target) {
    const names = floors.map(f => `${f.id}(${f.num}): ${f.title}`).join(", ");
    return { error: `Floor "${floor_id}" not found. Available: ${names}` };
  }

  // Find the floor body for this floor
  // We need to find the floor block that starts after the target's match
  const startIdx = target.index;
  // Find <div class="floor-body">
  const bodyStart = html.indexOf('<div class="floor-body">', startIdx);
  if (bodyStart === -1) {
    return { error: "Could not find floor-body in target floor" };
  }
  const bodyContentStart = bodyStart + '<div class="floor-body">'.length;
  // Find matching </div> for floor-body
  // Simple approach: find </div> after bodyStart that's before next floor or footer
  const nextFloorIdx = html.indexOf('<!-- ======', bodyContentStart);
  const footerIdx = html.indexOf('<div class="footer">', bodyContentStart);
  let bodyEnd = Math.min(
    nextFloorIdx !== -1 ? nextFloorIdx : Infinity,
    footerIdx !== -1 ? footerIdx : Infinity
  );
  if (bodyEnd === Infinity) {
    bodyEnd = html.indexOf('</body>', bodyContentStart);
  }
  if (bodyEnd === -1) {
    return { error: "Could not find end of floor block" };
  }

  // Find the last </div> before the end marker
  const closingDiv = html.lastIndexOf('</div>', bodyEnd);
  if (closingDiv === -1 || closingDiv <= bodyContentStart) {
    return { error: "Could not find closing </div> for floor-body" };
  }

  html = html.slice(0, bodyContentStart) + "\n    " + content + "\n  " + html.slice(closingDiv);
  writeHTML(building, html);

  return {
    building: BUILDINGS[building].name,
    floor: floor_id,
    title: target.title,
    message: `已更新 ${BUILDINGS[building].name} · ${floor_id} · "${target.title}"`,
  };
}

/**
 * 魔都_read_building
 * Read the current structure of a building (floors list).
 */
async function readBuilding(args) {
  const { building } = args;
  if (!BUILDINGS[building]) {
    return { error: `Unknown building: ${building}. Use: physics, computer, math, philosophy` };
  }

  const html = readHTML(building);
  const floors = parseFloors(html);

  let output = `# ${BUILDINGS[building].name}\n`;
  output += `文件: ${BUILDINGS[building].file}\n\n`;
  if (floors.length === 0) {
    output += "(无法解析楼层——检查 HTML 结构)\n";
  } else {
    for (const f of floors) {
      output += `- **${f.id}** (${f.num}): ${f.title}\n`;
    }
  }
  output += `\n共 ${floors.length} 层。`;

  return {
    building: BUILDINGS[building].name,
    floor_count: floors.length,
    floors: floors.map(f => ({ id: f.id, num: f.num, title: f.title })),
    message: output,
  };
}

/**
 * 魔都_list_buildings
 * List all three buildings with summaries.
 */
async function listBuildings() {
  const results = [];
  for (const [key, b] of Object.entries(BUILDINGS)) {
    const html = readHTML(key);
    const floors = parseFloors(html);
    results.push({
      key,
      name: b.name,
      file: b.file,
      description: b.description,
      floor_count: floors.length,
      last_floor: floors.length > 0 ? `${floors[floors.length - 1].num}: ${floors[floors.length - 1].title}` : "none",
    });
  }
  return {
    buildings: results,
    message: results.map(r =>
      `**${r.name}** (${r.key}) · ${r.floor_count} 层 · 末层: ${r.last_floor}\n  ${r.description}`
    ).join("\n\n"),
  };
}

// ============================================================
// MCP Server
// ============================================================
const server = new Server(
  {
    name: "魔都三件套",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "魔都_add_finding",
      description: "向魔都三件套的某座大厦添加一个新楼层。用法：在对话中产生了有效进度或精华结论时，调用此工具将其添加到对应大厦。building 可选: physics(物理大厦), computer(物理计算机大厦), math(数学大厦)。content 为 HTML 格式的楼层内容。",
      inputSchema: {
        type: "object",
        properties: {
          building: {
            type: "string",
            description: "大厦标识: physics, computer, math, philosophy",
            enum: ["physics", "computer", "math", "philosophy"],
          },
          title: {
            type: "string",
            description: "楼层标题（简短·10 字以内）",
          },
          content: {
            type: "string",
            description: "楼层正文，HTML 格式。支持 <h3>, <p>, <table>, <div class='theorem'>, <div class='insight'>, <ul>, <strong> 等标签。",
          },
        },
        required: ["building", "title", "content"],
      },
    },
    {
      name: "魔都_update_floor",
      description: "更新某座大厦某个已有楼层的内容。用于修正或补充已有楼层。",
      inputSchema: {
        type: "object",
        properties: {
          building: {
            type: "string",
            description: "大厦标识: physics, computer, math, philosophy",
            enum: ["physics", "computer", "math", "philosophy"],
          },
          floor_id: {
            type: "string",
            description: "楼层标识，如 '1F', '2F', 'F0', '⊤' 等。用 魔都_read_building 查看可用楼层。",
          },
          content: {
            type: "string",
            description: "新的楼层正文，HTML 格式。",
          },
        },
        required: ["building", "floor_id", "content"],
      },
    },
    {
      name: "魔都_read_building",
      description: "读取某座大厦的当前楼层结构和摘要。用于查看现有楼层以决定在哪更新。",
      inputSchema: {
        type: "object",
        properties: {
          building: {
            type: "string",
            description: "大厦标识: physics, computer, math, philosophy",
            enum: ["physics", "computer", "math", "philosophy"],
          },
        },
        required: ["building"],
      },
    },
    {
      name: "魔都_list_buildings",
      description: "列出三座大厦的概况——每座多少层、末层是什么。",
      inputSchema: {
        type: "object",
        properties: {},
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    let result;
    switch (name) {
      case "魔都_add_finding":
        result = await addFinding(args);
        break;
      case "魔都_update_floor":
        result = await updateFloor(args);
        break;
      case "魔都_read_building":
        result = await readBuilding(args);
        break;
      case "魔都_list_buildings":
        result = await listBuildings();
        break;
      default:
        return { content: [{ type: "text", text: `Unknown tool: ${name}` }], isError: true };
    }

    if (result.error) {
      return { content: [{ type: "text", text: result.error }], isError: true };
    }

    return {
      content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
    };
  } catch (err) {
    return {
      content: [{ type: "text", text: `Error: ${err.message}\n${err.stack}` }],
      isError: true,
    };
  }
});

// ============================================================
// Main
// ============================================================
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(console.error);
