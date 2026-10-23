"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Wrench } from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";
import { Controller, useForm } from "react-hook-form";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useCreateAction } from "@/lib/api/hooks";
import { titleCase } from "@/lib/utils";

const schema = z.object({
  title: z.string().trim().min(6, "Give the action a clear title."),
  description: z.string().trim().min(12, "Describe what should happen and why."),
  owner_role: z.enum(["analyst", "admin", "approver"]),
  due_date: z.string().optional(),
  priority: z.enum(["low", "medium", "high", "critical"]),
});

type Values = z.infer<typeof schema>;

export function AddActionDialog({
  riskId,
  open,
  onOpenChange,
}: {
  riskId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const t = useTranslations("risks");
  const common = useTranslations("common");
  const createAction = useCreateAction(riskId);
  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: {
      title: "",
      description: "",
      owner_role: "analyst",
      due_date: "",
      priority: "medium",
    },
  });

  React.useEffect(() => {
    if (open) {
      reset({
        title: "",
        description: "",
        owner_role: "analyst",
        due_date: "",
        priority: "medium",
      });
    }
  }, [open, reset]);

  const onSubmit = handleSubmit(async (values) => {
    try {
      await createAction.mutateAsync({
        title: values.title,
        description: values.description,
        owner_role: values.owner_role,
        due_date: values.due_date || null,
        priority: values.priority,
      });
      toast.success(t("actionCreated"), {
        description: "The draft is ready for a human approval request.",
      });
      onOpenChange(false);
      reset();
    } catch (error) {
      toast.error("Could not create the action.", {
        description: error instanceof Error ? error.message : undefined,
      });
    }
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <div className="mb-1 flex size-9 items-center justify-center rounded-lg border border-accent/20 bg-accent/10 text-accent">
            <Wrench className="size-4" />
          </div>
          <DialogTitle>{t("addActionTitle")}</DialogTitle>
          <DialogDescription>{t("addActionSub")}</DialogDescription>
        </DialogHeader>

        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="action-title">{t("actionTitle")}</Label>
            <Input
              id="action-title"
              {...register("title")}
              placeholder="e.g. Verify supplier payroll records with an independent auditor"
            />
            {errors.title ? (
              <p className="text-[10px] text-rose-300">{errors.title.message}</p>
            ) : null}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="action-description">{t("actionDescription")}</Label>
            <Textarea
              id="action-description"
              {...register("description")}
              placeholder="What evidence will be collected, by whom, and by when?"
              className="min-h-24"
            />
            {errors.description ? (
              <p className="text-[10px] text-rose-300">{errors.description.message}</p>
            ) : null}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>{t("ownerRole")}</Label>
              <Controller
                control={control}
                name="owner_role"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {["analyst", "admin", "approver"].map((role) => (
                        <SelectItem key={role} value={role}>
                          {titleCase(role)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
            <div className="space-y-1.5">
              <Label>{common("priority")}</Label>
              <Controller
                control={control}
                name="priority"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {["low", "medium", "high", "critical"].map((priority) => (
                        <SelectItem key={priority} value={priority}>
                          {titleCase(priority)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="due-date">{t("dueDate")}</Label>
            <Input id="due-date" type="date" {...register("due_date")} />
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              {common("cancel")}
            </Button>
            <Button type="submit" loading={createAction.isPending}>
              <Plus />
              {t("addAction")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
