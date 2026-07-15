"use client";

import { motion } from "framer-motion";
import { LAYOUT_CONFIG } from "@/config/layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  TrendingUp, TrendingDown, Activity, DollarSign, BrainCircuit, 
  Newspaper, Calendar, ArrowUpRight, ArrowDownRight, Clock,
  FileText, Play, Plus
} from "lucide-react";

// Animation Variants
const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
};

export default function DashboardPage() {
  return (
    <div className="w-full" style={{ padding: LAYOUT_CONFIG.content.padding }}>
      <motion.div 
        variants={container}
        initial="hidden"
        animate="show"
        className="flex flex-col gap-8 max-w-7xl mx-auto"
      >
        {/* 1. Greeting */}
        <motion.div variants={item}>
          <h1 className="text-3xl font-bold tracking-tight mb-2">Good Afternoon, Shreyash 👋</h1>
          <p className="text-muted-foreground">
            Here&apos;s what&apos;s happening with your portfolio today.
          </p>
        </motion.div>
        
        {/* 2. AI Daily Summary (Hero Card) */}
        <motion.div variants={item}>
          <Card className="bg-primary/5 border-primary/20 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
              <BrainCircuit className="w-32 h-32 text-primary" />
            </div>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-primary">
                <BrainCircuit className="w-5 h-5" />
                AI Daily Briefing
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-3 gap-6 relative z-10">
                <div className="col-span-2 space-y-4">
                  <p className="text-sm leading-relaxed">
                    Based on overnight filings and earnings calls, the technology sector is showing strong momentum. 
                    <strong className="text-foreground"> Apple Inc. (AAPL)</strong> reported Q3 earnings exceeding estimates by 12%, driven by services growth. 
                    We have flagged 3 companies in your watchlist for potential rating upgrades.
                  </p>
                  <Button size="sm" className="bg-primary text-primary-foreground hover:bg-primary/90">
                    Read Full Analysis
                  </Button>
                </div>
                <div className="border-l border-border/50 pl-6 space-y-4">
                  <div>
                    <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Portfolio Health</p>
                    <div className="flex items-end gap-2">
                      <span className="text-3xl font-bold text-emerald-500">92</span>
                      <span className="text-sm text-emerald-500 font-medium mb-1">Excellent</span>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Documents Processed</p>
                    <p className="text-2xl font-bold">146 <span className="text-sm text-muted-foreground font-normal">this week</span></p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* 3. Market Overview + Portfolio Summary */}
        <div className="grid lg:grid-cols-3 gap-6">
          <motion.div variants={item} className="lg:col-span-2">
            <Card className="h-full">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <div>
                  <CardTitle>Portfolio Overview</CardTitle>
                  <CardDescription>Value projection over the last 30 days</CardDescription>
                </div>
                <Button variant="ghost" size="sm">View All</Button>
              </CardHeader>
              <CardContent>
                <div className="h-[250px] w-full flex items-end gap-2 pt-4">
                  {/* Mock Chart using CSS for aesthetics */}
                  {[40, 30, 45, 50, 45, 60, 70, 65, 80, 85, 90, 100].map((h, i) => (
                    <div key={i} className="relative flex-1 group">
                      <motion.div 
                        initial={{ height: 0 }}
                        animate={{ height: `${h}%` }}
                        transition={{ duration: 1, delay: i * 0.05 }}
                        className="absolute bottom-0 w-full bg-primary/20 rounded-t-sm group-hover:bg-primary/40 transition-colors"
                      />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={item} className="space-y-6">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Value</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">$124,563.00</div>
                <p className="text-xs text-emerald-500 flex items-center mt-1">
                  <ArrowUpRight className="w-3 h-3 mr-1" />
                  +2.5% from last month
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Active Capital</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">$45,231.89</div>
                <p className="text-xs text-rose-500 flex items-center mt-1">
                  <ArrowDownRight className="w-3 h-3 mr-1" />
                  -0.8% from last month
                </p>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* 4. Watchlist + Recent Reports */}
        <div className="grid lg:grid-cols-2 gap-6">
          <motion.div variants={item}>
            <Card className="h-full">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Watchlist Intelligence</CardTitle>
                <Button variant="ghost" size="sm">Manage</Button>
              </CardHeader>
              <CardContent className="space-y-4">
                {[
                  { sym: "AAPL", name: "Apple Inc.", price: "$228.15", change: "+1.34%", up: true, score: 92 },
                  { sym: "MSFT", name: "Microsoft Corp.", price: "$412.30", change: "-0.54%", up: false, score: 88 },
                  { sym: "TSLA", name: "Tesla Inc.", price: "$245.89", change: "+4.21%", up: true, score: 74 },
                ].map((stock) => (
                  <div key={stock.sym} className="flex items-center justify-between p-3 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer border border-transparent hover:border-border/50">
                    <div className="flex items-center gap-4">
                      <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center font-bold text-primary text-xs">
                        {stock.sym}
                      </div>
                      <div>
                        <p className="font-semibold text-sm">{stock.name}</p>
                        <p className="text-xs text-muted-foreground">Health Score: <span className={stock.score > 80 ? "text-emerald-500" : "text-amber-500"}>{stock.score}</span></p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-sm">{stock.price}</p>
                      <p className={`text-xs flex items-center justify-end ${stock.up ? 'text-emerald-500' : 'text-rose-500'}`}>
                        {stock.up ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                        {stock.change}
                      </p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={item}>
            <Card className="h-full">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Recent Reports</CardTitle>
                <Button variant="ghost" size="sm">View All</Button>
              </CardHeader>
              <CardContent className="space-y-4">
                {[
                  { title: "AAPL Q3 2024 Investment Analysis", date: "2 hours ago", type: "Investment Report" },
                  { title: "TSLA Risk Assessment Matrix", date: "5 hours ago", type: "Risk Analysis" },
                  { title: "Tech Sector Q3 Earnings Preview", date: "Yesterday", type: "Sector Overview" },
                ].map((report, i) => (
                  <div key={i} className="flex items-start gap-4 p-3 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer border border-transparent hover:border-border/50">
                    <div className="mt-0.5 p-2 rounded-md bg-secondary/50 text-muted-foreground">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="font-medium text-sm text-foreground">{report.title}</p>
                      <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                        <span className="bg-background px-2 py-0.5 rounded-full border border-border/50">{report.type}</span>
                        <span>•</span>
                        <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{report.date}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* 5. Quick Actions */}
        <motion.div variants={item}>
          <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { icon: Plus, label: "New Analysis" },
              { icon: FileText, label: "Upload Document" },
              { icon: Activity, label: "Add to Watchlist" },
              { icon: BrainCircuit, label: "Ask AI Assistant" },
            ].map((action, i) => (
              <Button key={i} variant="outline" className="h-24 flex flex-col items-center justify-center gap-2 bg-background/40 hover:bg-background/80 transition-all">
                <action.icon className="w-6 h-6 text-primary" />
                <span className="text-xs font-medium">{action.label}</span>
              </Button>
            ))}
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
}
