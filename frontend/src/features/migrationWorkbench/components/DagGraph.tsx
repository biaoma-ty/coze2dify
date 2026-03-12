import { useId } from "react";
import { C, NODE_COLORS, NODE_ICONS } from "../theme";
import type { DagGraphData } from "../types";

interface DagGraphProps {
  graph: DagGraphData;
  platform: "coze" | "dify";
}

export default function DagGraph({ graph, platform }: DagGraphProps) {
  const markerId = useId();
  const stroke = platform === "coze" ? C.coze : C.dify;

  return (
    <svg width="100%" viewBox="0 0 980 320" role="img" aria-label={`${platform} dag`}>
      <defs>
        <marker
          id={markerId}
          markerWidth="8"
          markerHeight="6"
          refX="8"
          refY="3"
          orient="auto"
        >
          <polygon points="0 0,8 3,0 6" fill={stroke} opacity="0.55" />
        </marker>
      </defs>

      {graph.edges.map(([fromId, toId], index) => {
        const fromNode = graph.nodes.find((node) => node.id === fromId);
        const toNode = graph.nodes.find((node) => node.id === toId);

        if (!fromNode || !toNode) {
          return null;
        }

        const startX = fromNode.x + 55;
        const endX = toNode.x - 5;
        const controlX = (startX + endX) / 2;

        return (
          <path
            key={`${fromId}-${toId}-${index}`}
            d={`M${startX},${fromNode.y} C${controlX},${fromNode.y} ${controlX},${toNode.y} ${endX},${toNode.y}`}
            fill="none"
            markerEnd={`url(#${markerId})`}
            opacity="0.4"
            stroke={stroke}
            strokeWidth="1.6"
          />
        );
      })}

      {graph.nodes.map((node) => {
        const color = NODE_COLORS[node.type];
        const icon = NODE_ICONS[node.type];

        return (
          <g key={node.id}>
            <rect
              x={node.x - 5}
              y={node.y - 18}
              width={110}
              height={36}
              rx={7}
              fill={C.s1}
              stroke={color}
              strokeWidth="1"
              opacity="0.9"
            />
            <text
              x={node.x + 8}
              y={node.y + 2}
              fontSize="10"
              fill={C.tx}
              fontFamily={C.ft}
              dominantBaseline="middle"
              fontWeight="500"
            >
              {icon} {node.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
