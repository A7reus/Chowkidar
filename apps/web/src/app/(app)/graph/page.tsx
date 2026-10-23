"use client";

import {
  Background,
  BackgroundVariant,
  Controls,
  MarkerType,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import {
  ArrowUpRight,
  Building2,
  Factory,
  FileText,
  Info,
  Network,
  Scale,
  Search,
  ShieldAlert,
  Waypoints,
} from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import * as React from "react";

import { PageHeader } from "@/components/common/page-header";
import { PriorityBadge } from "@/components/common/badges";
import { ErrorState, PageSkeleton } from "@/components/common/states";
import {
  edgeColors,
  nodeTypes,
  type SupplyNodeType,
} from "@/components/graph/supply-chain-node";
import { Button } from "@/components/ui/button";
import { useGraph } from "@/lib/api/hooks";
import type { GraphData } from "@/lib/api/types";
import { cn, titleCase } from "@/lib/utils";

const kindMeta = {
  company: { icon: Building2, label: "Company", color: "#2dd4bf", className: "text-teal-300" },
  supplier: { icon: Factory, label: "Supplier", color: "#64748b", className: "text-slate-300" },
  risk: { icon: ShieldAlert, label: "Risk", color: "#fb7185", className: "text-rose-300" },
  obligation: { icon: Scale, label: "Obligation", color: "#38bdf8", className: "text-sky-300" },
  policy: { icon: FileText, label: "Policy", color: "#a78bfa", className: "text-violet-300" },
} as const;

const columnX: Record<keyof typeof kindMeta, number> = {
  company: 0,
  policy: 240,
  supplier: 480,
  risk: 720,
  obligation: 960,
};

function buildElements(data: GraphData) {
  const groups: Record<keyof typeof kindMeta, GraphData["nodes"]> = {
    company: [],
    supplier: [],
    risk: [],
    obligation: [],
    policy: [],
  };
  for (const node of data.nodes) groups[node.kind].push(node);

  const nodes: SupplyNodeType[] = data.nodes.map((node) => {
    const index = groups[node.kind].findIndex((item) => item.id === node.id);
    const y =
      node.kind === "company"
        ? 30
        : node.kind === "policy"
          ? 140 + index * 88
          : 10 + index * 88;
    return {
      id: node.id,
      type: "supply",
      position: { x: columnX[node.kind], y },
      data: {
        label: node.label,
        kind: node.kind,
        detail: node.detail,
        priority: node.priority,
      },
    };
  });

  const edges: Edge[] = data.edges.map((edge) => {
    const involvesRisk = edge.source.startsWith("risk:") || edge.target.startsWith("risk:");
    const color = edge.source.startsWith("risk:")
      ? edgeColors.risk
      : edge.source.startsWith("company:")
        ? edgeColors.company
        : edge.target.startsWith("obligation:")
          ? edgeColors.obligation
          : edgeColors.supplier;
    return {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: "smoothstep",
      animated: involvesRisk,
      style: {
        stroke: color,
        strokeWidth: involvesRisk ? 1.4 : 1,
        strokeOpacity: involvesRisk ? 0.8 : 0.5,
      },
      markerEnd: { type: MarkerType.ArrowClosed, color, width: 13, height: 13 },
    };
  });

  return { nodes, edges };
}

function NodeInspector({
  graph,
  selectedId,
}: {
  graph: GraphData;
  selectedId: string | null;
}) {
  const selected = graph.nodes.find((node) => node.id === selectedId);
  const connections = selected
    ? graph.edges.filter((edge) => edge.source === selected.id || edge.target === selected.id)
    : [];

  if (!selected) {
    return (
      <div className="panel flex min-h-[150px] items-center gap-4 p-5">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-xl border border-border bg-white/[0.025] text-muted">
          <Waypoints className="size-4" />
        </div>
        <div>
          <p className="font-display text-sm font-semibold text-slate-100">Select a node</p>
          <p className="mt-1 text-[10px] leading-relaxed text-muted">
            Click any node in the graph to inspect its relationships and open the linked record.
          </p>
        </div>
      </div>
    );
  }

  const meta = kindMeta[selected.kind];
  const Icon = meta.icon;
  const riskId = selected.kind === "risk" ? selected.id.replace("risk:", "") : null;

  return (
    <div className="panel p-5">
      <div className="grid gap-5 lg:grid-cols-[320px_minmax(0,1fr)]">
        <div>
          <div className="flex items-start gap-3">
            <div className="flex size-9 shrink-0 items-center justify-center rounded-lg border border-border bg-white/[0.025]">
              <Icon className={cn("size-4", meta.className)} />
            </div>
            <div className="min-w-0">
              <p className="text-[9px] font-semibold uppercase tracking-[0.16em] text-muted-2">
                {meta.label} · node inspector
              </p>
              <h2 className="mt-1 font-display text-[15px] font-semibold leading-snug text-slate-100">
                {selected.label}
              </h2>
              {selected.detail ? <p className="mt-1 text-[10px] text-muted">{selected.detail}</p> : null}
            </div>
          </div>

          {selected.priority ? (
            <div className="mt-3 flex items-center gap-2">
              <PriorityBadge priority={selected.priority} />
              <span className="text-[9px] text-muted-2">prioritized risk</span>
            </div>
          ) : null}

          {riskId ? (
            <Button asChild className="mt-4 w-full" size="sm">
              <Link href={`/risks/${riskId}`}>
                Open risk detail
                <ArrowUpRight />
              </Link>
            </Button>
          ) : null}

          <div className="mt-4 rounded-lg border border-border-soft bg-white/[0.015] p-3">
            <div className="flex items-start gap-2">
              <Info className="mt-0.5 size-3 shrink-0 text-muted-2" />
              <p className="text-[9px] leading-relaxed text-muted-2">
                Node IDs map directly to operational records. In production, the same projection is
                materialized in Neo4j Aura.
              </p>
            </div>
          </div>
        </div>

        <div className="min-w-0">
          <div className="flex items-center justify-between">
            <p className="text-[9px] font-semibold uppercase tracking-[0.14em] text-muted-2">
              Connections
            </p>
            <span className="rounded border border-border bg-white/[0.02] px-1.5 py-0.5 font-mono text-[8px] text-muted-2">
              {connections.length}
            </span>
          </div>
          <div className="mt-2 grid gap-1.5 sm:grid-cols-2">
            {connections.length === 0 ? (
              <p className="text-[10px] text-muted-2">No graph connections.</p>
            ) : (
              connections.slice(0, 12).map((edge) => {
                const otherId = edge.source === selected.id ? edge.target : edge.source;
                const other = graph.nodes.find((node) => node.id === otherId);
                if (!other) return null;
                const otherMeta = kindMeta[other.kind];
                const OtherIcon = otherMeta.icon;
                return (
                  <div
                    key={edge.id}
                    className="flex items-start gap-2 rounded-lg border border-border-soft bg-white/[0.015] p-2"
                  >
                    <OtherIcon className={cn("mt-0.5 size-3 shrink-0", otherMeta.className)} />
                    <div className="min-w-0">
                      <p className="line-clamp-1 text-[10px] text-slate-300">{other.label}</p>
                      <p className="text-[8px] text-muted-2">
                        {edge.source === selected.id ? "→" : "←"} {edge.label}
                      </p>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function GraphPage() {
  const t = useTranslations("graph");
  const graph = useGraph();
  const [selectedId, setSelectedId] = React.useState<string | null>(null);

  const elements = React.useMemo(
    () => (graph.data ? buildElements(graph.data) : { nodes: [], edges: [] }),
    [graph.data],
  );

  if (graph.isLoading) return <PageSkeleton cards={0} />;
  if (graph.isError) {
    return <ErrorState error={graph.error} onRetry={() => void graph.refetch()} />;
  }
  if (!graph.data) return <PageSkeleton cards={0} />;

  const defaultRiskId = graph.data.nodes.find((node) => node.kind === "risk")?.id ?? null;
  const effectiveSelectedId = selectedId ?? defaultRiskId;

  const counts = graph.data.nodes.reduce<Record<string, number>>((acc, node) => {
    acc[node.kind] = (acc[node.kind] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="Intelligence · Relationships" title={t("title")} description={t("subtitle")}>
        <Button variant="secondary" asChild>
          <Link href="/search">
            <Search />
            Evidence search
          </Link>
        </Button>
        <Button asChild>
          <Link href="/risks">
            <ShieldAlert />
            Risk register
          </Link>
        </Button>
      </PageHeader>

      <div className="flex flex-wrap items-center gap-2">
        {(Object.keys(kindMeta) as Array<keyof typeof kindMeta>).map((kind) => {
          const meta = kindMeta[kind];
          const Icon = meta.icon;
          return (
            <span
              key={kind}
              className="flex items-center gap-1.5 rounded-lg border border-border bg-white/[0.02] px-2.5 py-1 text-[10px] text-muted"
            >
              <Icon className={cn("size-3", meta.className)} />
              {meta.label}
              <span className="font-mono text-[9px] text-muted-2">{counts[kind] ?? 0}</span>
            </span>
          );
        })}
        <span className="ml-auto flex items-center gap-1.5 text-[9px] text-muted-2">
          <Network className="size-3" />
          {graph.data.nodes.length} {t("nodes")} · {graph.data.edges.length} {t("edges")}
        </span>
      </div>

      <div className="grid gap-4">
        <div className="panel relative h-[640px] overflow-hidden">
          <div className="pointer-events-none absolute left-3 top-3 z-10 rounded-lg border border-border bg-[#08101d]/90 px-2.5 py-1.5 text-[9px] text-muted-2 backdrop-blur">
            {t("clickHint")}
          </div>
          <ReactFlow
            defaultNodes={elements.nodes}
            defaultEdges={elements.edges}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.04 }}
            minZoom={0.4}
            maxZoom={1.8}
            nodesDraggable
            nodesConnectable={false}
            elementsSelectable
            onInit={(instance) => {
              window.setTimeout(() => {
                void instance.fitView({ padding: 0.04 });
              }, 60);
            }}
            onNodeClick={(_event: React.MouseEvent, node: Node) => setSelectedId(node.id)}
            onPaneClick={() => setSelectedId("")}
            className="h-full w-full"
          >
            <Background variant={BackgroundVariant.Dots} gap={18} size={1} color="#1a2a42" />
            <Controls showInteractive={false} position="bottom-left" />
          </ReactFlow>
        </div>
        <NodeInspector graph={graph.data} selectedId={effectiveSelectedId} />
      </div>

      <div className="flex flex-wrap items-center gap-2 text-[10px] text-muted-2">
        <Info className="size-3" />
        {t("source")}
        <span className="ml-auto flex items-center gap-1.5">
          <span className="size-1.5 rounded-full bg-rose-400" /> animated edges connect risks
        </span>
      </div>
      <p className="px-1 text-[10px] leading-relaxed text-muted-2">
        Graph relationships are derived from the same risk register used for the audit pack. A
        relationship is a prompt for review, not a legal conclusion. {titleCase("not legal advice")}.
      </p>
    </div>
  );
}
