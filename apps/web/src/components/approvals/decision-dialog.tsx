"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { CheckCircle2, ShieldQuestion } from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useDecideApproval } from "@/lib/api/hooks";
import type { Approval } from "@/lib/api/types";
import { cn } from "@/lib/utils";

const schema = z.object({
  rationale: z
    .string()
    .trim()
    .min(12, "Write at least 12 characters so the decision is reviewable.")
    .max(2000, "Keep the rationale under 2,000 characters."),
});

type Values = z.infer<typeof schema>;

export function ApprovalDecisionDialog({
  approval,
  decision,
  open,
  onOpenChange,
}: {
  approval: Approval | null;
  decision: "approve" | "reject";
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const t = useTranslations("approvals");
  const decide = useDecideApproval();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { rationale: "" },
  });

  React.useEffect(() => {
    if (open) reset({ rationale: "" });
  }, [open, reset]);

  const onSubmit = handleSubmit(async (values) => {
    if (!approval) return;
    try {
      await decide.mutateAsync({
        approvalId: approval.id,
        riskId: approval.risk_id,
        decision,
        rationale: values.rationale,
      });
      toast.success(t("decided"), {
        description:
          decision === "approve"
            ? "The remediation was approved and written to the audit trail."
            : "The rejection was recorded in the audit trail.",
      });
      onOpenChange(false);
      reset();
    } catch (error) {
      toast.error("Could not record the decision.", {
        description: error instanceof Error ? error.message : undefined,
      });
    }
  });

  const isApprove = decision === "approve";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <div
            className={cn(
              "mb-1 flex size-9 items-center justify-center rounded-lg border",
              isApprove
                ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-300"
                : "border-rose-400/20 bg-rose-400/10 text-rose-300",
            )}
          >
            {isApprove ? <CheckCircle2 className="size-4" /> : <ShieldQuestion className="size-4" />}
          </div>
          <DialogTitle>{t(isApprove ? "approveTitle" : "rejectTitle")}</DialogTitle>
          <DialogDescription>{t("decisionSub")}</DialogDescription>
        </DialogHeader>

        {approval ? (
          <div className="rounded-lg border border-border-soft bg-white/[0.02] p-3">
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-2">
              {t("action")}
            </p>
            <p className="mt-1 text-sm font-medium text-slate-100">
              {approval.action_title ?? "Remediation action"}
            </p>
            <p className="mt-1 text-[11px] leading-relaxed text-muted">
              {approval.risk_title ?? "Risk record"}
            </p>
          </div>
        ) : null}

        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="rationale">{t("rationale")}</Label>
            <Textarea
              id="rationale"
              {...register("rationale")}
              placeholder={t("rationalePlaceholder")}
              className="min-h-28"
            />
            {errors.rationale ? (
              <p className="text-[10px] text-rose-300">{errors.rationale.message}</p>
            ) : (
              <p className="text-[10px] text-muted-2">
                This note becomes part of the immutable audit trail.
              </p>
            )}
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              {t("rationale") ? "Cancel" : "Cancel"}
            </Button>
            <Button
              type="submit"
              variant={isApprove ? "default" : "danger"}
              loading={decide.isPending}
            >
              {isApprove ? t("confirmApprove") : t("confirmReject")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
