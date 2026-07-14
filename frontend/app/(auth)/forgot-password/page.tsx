"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, ArrowLeft, MailCheck } from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";

import {
  forgotPasswordSchema,
  type ForgotPasswordFormValues,
} from "@/types/auth.types";
import { useForgotPassword } from "@/features/auth/hooks/use-auth";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

import { AuthCard } from "@/components/auth/AuthCard";
import { AuthHeader } from "@/components/auth/AuthHeader";

export default function ForgotPasswordPage() {
  const [isSuccess, setIsSuccess] = React.useState(false);
  const { mutate: forgotPassword, isPending } = useForgotPassword();

  const form = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: "",
    },
  });

  const onSubmit = (data: ForgotPasswordFormValues) => {
    forgotPassword(data.email, {
      onSuccess: () => {
        setIsSuccess(true);
      },
    });
  };

  return (
    <AuthCard>
      <AnimatePresence mode="wait">
        {!isSuccess ? (
          <motion.div
            key="form"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            transition={{ duration: 0.3 }}
          >
            <AuthHeader
              title="Forgot your password?"
              description="Enter your email address and we will send you a reset link"
            />
            
            <div className="px-6 pb-6">
              <Form {...form}>
                <form
                  onSubmit={form.handleSubmit(onSubmit)}
                  className="space-y-4"
                >
                  <FormField
                    control={form.control}
                    name="email"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Email</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="name@example.com"
                            className="input-glow"
                            autoComplete="email"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="pt-2">
                    <Button type="submit" className="w-full" disabled={isPending}>
                      {isPending && (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      )}
                      {isPending ? "Sending link..." : "Send reset link"}
                    </Button>
                  </div>
                </form>
              </Form>

              <div className="mt-6 text-center">
                <Link
                  href="/login"
                  className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                >
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back to sign in
                </Link>
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="success"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4 }}
            className="flex flex-col items-center justify-center p-8 text-center space-y-4"
          >
            <motion.div 
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", stiffness: 300, damping: 20, delay: 0.2 }}
              className="w-16 h-16 rounded-full bg-emerald-500/10 flex items-center justify-center mb-2"
              aria-hidden="true"
            >
              <MailCheck className="w-8 h-8 text-emerald-500" />
            </motion.div>
            <h3 className="text-xl font-semibold tracking-tight mt-2">Check your email</h3>
            <p className="text-sm text-muted-foreground max-w-[280px]">
              We&apos;ve sent a password reset link to <br />
              <span className="font-medium text-foreground">
                {form.getValues().email}
              </span>
            </p>
            <Button
              variant="outline"
              className="mt-6 w-full"
              onClick={() => setIsSuccess(false)}
            >
              Try another email
            </Button>
            <div className="mt-4">
              <Link
                href="/login"
                className="text-sm font-medium text-primary hover:text-primary/80 transition-colors underline underline-offset-4"
              >
                Return to sign in
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </AuthCard>
  );
}
