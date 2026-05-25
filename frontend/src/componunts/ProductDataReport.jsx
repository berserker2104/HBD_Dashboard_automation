import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Card,
  CardBody,
  Typography,
  Button,
  Spinner,
  Chip,
  Input,
  IconButton,
} from "@material-tailwind/react";
import {
  StarIcon,
  FireIcon,
  ShoppingBagIcon,
  ArrowTopRightOnSquareIcon,
  TagIcon,
  ArchiveBoxIcon,
  CurrencyRupeeIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  InboxIcon,
  XMarkIcon,
  ChartBarIcon,
  TrophyIcon,
  CheckIcon,
  ClipboardIcon,
  ExclamationTriangleIcon,
  ArrowDownTrayIcon
} from "@heroicons/react/24/outline";
import { StarIcon as StarSolid } from "@heroicons/react/24/solid";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from "recharts";
import api from "../utils/Api";

// Curated SaaS Color Palette
const COLORS = {
  primary: "#3b82f6",     // vibrant blue
  secondary: "#8b5cf6",   // deep purple
  success: "#10b981",     // emerald green
  warning: "#f59e0b",     // amber yellow
  danger: "#ef4444",      // rose red
  gray: "#94a3b8",        // slate gray
  lightGray: "#f1f5f9",   // light slate
  dark: "#0f172a",        // dark navy slate
  muted: "#64748b",       // muted text
};

const StarRating = ({ value }) => {
  if (!value) return <span className="text-slate-400 text-xs font-normal">—</span>;
  const starsCount = Math.round(value);
  return (
    <div className="flex items-center gap-1">
      <div className="flex text-amber-400">
        {[...Array(5)].map((_, i) => (
          <StarSolid
            key={i}
            className={`h-4 w-4 ${i < starsCount ? "text-amber-400" : "text-slate-200"}`}
          />
        ))}
      </div>
      <span className="text-slate-600 font-semibold text-xs ml-1">
        {Number(value).toFixed(1)}
      </span>
    </div>
  );
};

export default function ProductDataReport() {
  const navigate = useNavigate();

  // Persisted States inside localStorage
  const [activeTab, setActiveTab] = useState(() => localStorage.getItem("activeTab") || "dashboard");
  const [marketplaceFilter, setMarketplaceFilter] = useState(() => localStorage.getItem("marketplaceFilter") || "All");
  const [categoryFilter, setCategoryFilter] = useState(() => localStorage.getItem("categoryFilter") || "All Categories");
  const [statusFilter, setStatusFilter] = useState(() => localStorage.getItem("statusFilter") || "All");
  const [dateRangeFilter, setDateRangeFilter] = useState(() => localStorage.getItem("dateRangeFilter") || "Last 30 Days");
  
  // Searching & Query States
  const [searchQuery, setSearchQuery] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");

  // Data States
  const [summary, setSummary] = useState(null);
  const [categoryCounts, setCategoryCounts] = useState(null);
  const [topProducts, setTopProducts] = useState([]);
  const [mappedCategories, setMappedCategories] = useState([]);
  const [unmappedCategories, setUnmappedCategories] = useState([]);
  const [unmappedProducts, setUnmappedProducts] = useState([]);

  // Detail Drawer States
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);

  // Global UI States
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Dropdown Lists precisely matching requirements
  const marketplacesList = ["All", "Amazon", "IndiaMART", "BigBasket", "DMart", "Blinkit", "JioMart", "Flipkart"];
  const statusList = ["All", "Mapped", "Unmapped", "Pending", "Completed"];
  const dateRangeList = ["Today", "Last 7 Days", "Last 30 Days"];

  // Sync state changes to localStorage
  useEffect(() => {
    localStorage.setItem("activeTab", activeTab);
  }, [activeTab]);

  useEffect(() => {
    localStorage.setItem("marketplaceFilter", marketplaceFilter);
  }, [marketplaceFilter]);

  useEffect(() => {
    localStorage.setItem("categoryFilter", categoryFilter);
  }, [categoryFilter]);

  useEffect(() => {
    localStorage.setItem("statusFilter", statusFilter);
  }, [statusFilter]);

  useEffect(() => {
    localStorage.setItem("dateRangeFilter", dateRangeFilter);
  }, [dateRangeFilter]);

  // Two-way synchronization between Status Filter dropdown and Active Navigation tabs
  useEffect(() => {
    if (statusFilter === "Mapped" || statusFilter === "Completed") {
      if (activeTab !== "mapped-categories") {
        setActiveTab("mapped-categories");
      }
    } else if (statusFilter === "Unmapped" || statusFilter === "Pending") {
      if (activeTab !== "unmapped-categories" && activeTab !== "unmapped-products") {
        setActiveTab("unmapped-categories");
      }
    } else if (statusFilter === "All") {
      if (activeTab !== "dashboard" && activeTab !== "top-selling") {
        setActiveTab("dashboard");
      }
    }
  }, [statusFilter]);

  useEffect(() => {
    if (activeTab === "mapped-categories") {
      if (statusFilter !== "Mapped" && statusFilter !== "Completed") {
        setStatusFilter("Mapped");
      }
    } else if (activeTab === "unmapped-categories" || activeTab === "unmapped-products") {
      if (statusFilter !== "Unmapped" && statusFilter !== "Pending") {
        setStatusFilter("Unmapped");
      }
    } else if (activeTab === "dashboard" || activeTab === "top-selling") {
      if (statusFilter !== "All") {
        setStatusFilter("All");
      }
    }
  }, [activeTab]);

  // Fetch Summary & Overview
  const fetchSummaryAndOverview = async () => {
    try {
      const marketParam = marketplaceFilter === "All" ? "all" : marketplaceFilter;
      const [sumRes, catCountRes] = await Promise.all([
        api.get(`/product-report/summary?marketplace=${marketParam}`),
        api.get(`/product-report/category-counts?marketplace=${marketParam}`),
      ]);

      setSummary(sumRes.data?.data || null);
      setCategoryCounts(catCountRes.data?.data || null);
    } catch (e) {
      console.error("Summary fetch error", e);
      setError("Failed to fetch dashboard summary.");
    }
  };

  // Fetch Tabular Content Data
  const fetchTabContent = async () => {
    setLoading(true);
    try {
      const marketParam = marketplaceFilter === "All" ? "all" : marketplaceFilter;
      const searchParam = appliedSearch ? encodeURIComponent(appliedSearch) : "";

      if (activeTab === "dashboard") {
        const topRes = await api.get(`/product-report/top-products?marketplace=${marketParam}&limit=10`);
        setTopProducts(topRes.data?.data || []);
      } else if (activeTab === "top-selling") {
        const topRes = await api.get(
          `/product-report/top-products?marketplace=${marketParam}&search=${searchParam}&category=${encodeURIComponent(categoryFilter)}&limit=50`
        );
        setTopProducts(topRes.data?.data || []);
      } else if (activeTab === "mapped-categories") {
        const mappedRes = await api.get(`/product-report/mapped-categories?marketplace=${marketParam}&search=${searchParam}`);
        setMappedCategories(mappedRes.data?.data || []);
      } else if (activeTab === "unmapped-categories") {
        const unmappedCatRes = await api.get(`/product-report/unmapped-categories?marketplace=${marketParam}&search=${searchParam}`);
        setUnmappedCategories(unmappedCatRes.data?.data || []);
      } else if (activeTab === "unmapped-products") {
        const unmappedProdRes = await api.get(`/product-report/unmapped-products?marketplace=${marketParam}&search=${searchParam}`);
        setUnmappedProducts(unmappedProdRes.data?.data || []);
      }
    } catch (e) {
      console.error("Content fetch error", e);
      setError("Failed to fetch data for the requested section.");
    } finally {
      setLoading(false);
    }
  };

  // Trigger loading of data when options or filters change
  useEffect(() => {
    const loadAll = async () => {
      setError(null);
      await fetchSummaryAndOverview();
      await fetchTabContent();
    };
    loadAll();
  }, [marketplaceFilter, activeTab, appliedSearch, categoryFilter]);

  // Handle Search Submission
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setAppliedSearch(searchQuery);
  };

  // Trigger manual refresh & native browser reload to update dashboard data
  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const marketParam = marketplaceFilter === "All" ? "all" : marketplaceFilter;
      await api.post(`/product-report/refresh?marketplace=${marketParam}`);
    } catch (e) {
      console.error("Refresh API error", e);
    } finally {
      setRefreshing(false);
      window.location.reload(); // Native reload preserving selections
    }
  };

  // Export current data matrix to CSV
  const handleExportData = () => {
    let csvContent = "data:text/csv;charset=utf-8,";
    
    if (activeTab === "top-selling") {
      csvContent += "Rank,Marketplace,Product ID,ASIN,Product Name,Brand,Category,Price,Stars,Reviews,Velocity,Score\n";
      topProducts.forEach((p, idx) => {
        csvContent += `"${idx+1}","${p.marketplace_name}","${p.product_id}","${p.asin}","${p.product_name?.replace(/"/g, '""')}","${p.brand}","${p.category_name}",${p.price},${p.stars},${p.reviews},${p.bought_in_last_month},${p.ranking_score}\n`;
      });
    } else if (activeTab === "mapped-categories") {
      csvContent += "Category ID,Marketplace,Level,Path Tree\n";
      mappedCategories.forEach((c) => {
        csvContent += `"${c.id}","${c.marketplace_name}","L${c.category_level}","${c.category_path?.replace(/"/g, '""')}"\n`;
      });
    } else if (activeTab === "unmapped-categories") {
      csvContent += "Exception ID,Marketplace,Path Tree,Rejection Reason\n";
      unmappedCategories.forEach((c) => {
        csvContent += `"${c.category_id || c.id}","${c.marketplace_name}","${c.category_path?.replace(/"/g, '""')}","${c.reason?.replace(/"/g, '""')}"\n`;
      });
    } else if (activeTab === "unmapped-products") {
      csvContent += "ID/ASIN,Marketplace,Product Name,Brand,Category,Rejection Reason\n";
      unmappedProducts.forEach((p) => {
        csvContent += `"${p.asin || p.product_id}","${p.marketplace_name}","${p.product_name?.replace(/"/g, '""')}","${p.brand}","${p.category_name}","${p.reason?.replace(/"/g, '""')}"\n`;
      });
    } else {
      csvContent += "Metric,Value\n";
      if (summary) {
        csvContent += `"Total Products Ingested","${summary.total_products}"\n`;
        csvContent += `"Successfully Mapped Products","${summary.mapped_products}"\n`;
        csvContent += `"Available Products Stock","${summary.available_products}"\n`;
        csvContent += `"Completed Categories","${summary.completed_categories}"\n`;
        csvContent += `"Pending Categories","${summary.pending_categories}"\n`;
        csvContent += `"Average Selling Price","₹${summary.avg_selling_price}"\n`;
      }
    }

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `Product_Data_Report_${activeTab}_${marketplaceFilter}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Open specs drawer
  const openProductDrawer = async (product) => {
    setIsDrawerOpen(true);
    setDrawerLoading(true);
    setSelectedProduct(null);
    setCopySuccess(false);

    try {
      let detailRes;
      const isAmazon = product.marketplace_name?.toLowerCase() === "amazon";

      if (isAmazon && product.asin) {
        detailRes = await api.get(`/product-report/products/amazon/${product.asin}`);
      } else {
        const idToLookup = product.product_id || product.id;
        const marketName = product.marketplace_name || marketplaceFilter;
        detailRes = await api.get(`/product-report/products/${marketName}/${idToLookup}`);
      }

      if (detailRes.data?.status === "success") {
        setSelectedProduct(detailRes.data.data);
      } else {
        setSelectedProduct(product); 
      }
    } catch (e) {
      console.error("Failed to load deep product details", e);
      setSelectedProduct(product); 
    } finally {
      setDrawerLoading(false);
    }
  };

  // Copy ASIN / ID to clipboard
  const handleCopyToClipboard = (text) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  // Pie Data
  const getPieChartData = () => {
    if (!categoryCounts || categoryCounts.total_categories === 0) return [];
    return [
      { name: "Completed Mapping", value: Number(categoryCounts.completed_categories), color: COLORS.success },
      { name: "Pending Mapping", value: Number(categoryCounts.pending_categories), color: COLORS.warning },
    ];
  };

  // Stacked Bar Data
  const getProductBarData = () => {
    if (!summary || summary.total_products === 0) return [];
    return [
      {
        name: "Products Status",
        Mapped: Number(summary.mapped_products),
        Unmapped: Number(summary.unmapped_products),
      },
    ];
  };

  const isPendingUpload = summary && summary.status_badge === "Pending Data Upload";

  return (
    <div className="flex flex-col gap-6 mt-4 mb-12 px-4 xl:px-8 text-slate-800 w-full max-w-[1600px] mx-auto">
      
      {/* ========================================================
          STICKY TOP NAVBAR FILTER MATRIX (Exactly conforming)
         ======================================================== */}
      <Card className="border border-slate-100 shadow-sm rounded-2xl overflow-visible bg-white/85 backdrop-blur-md sticky top-0 z-40">
        <CardBody className="p-4 flex flex-col xl:flex-row items-center justify-between gap-4">
          
          {/* Dropdown Filters matrix Group */}
          <div className="flex items-center gap-2.5 flex-wrap w-full xl:w-auto">
            
            {/* Marketplace Dropdown filter */}
            <div className="flex flex-col gap-1 min-w-[130px]">
              <span className="text-[10px] text-slate-400 font-extrabold uppercase tracking-wide">Marketplace</span>
              <div className="relative">
                <select
                  value={marketplaceFilter}
                  onChange={(e) => setMarketplaceFilter(e.target.value)}
                  className="appearance-none w-full bg-slate-50 border border-slate-200 text-slate-800 text-xs font-bold rounded-xl pl-4 pr-10 py-2.5 outline-none hover:bg-slate-100/70 transition-all duration-200 cursor-pointer focus:border-blue-500"
                >
                  {marketplacesList.map((m) => (
                    <option key={m} value={m}>
                      {m === "All" ? "All" : m}
                    </option>
                  ))}
                </select>
                <ArrowPathIcon className="h-3 w-3 text-slate-400 absolute right-3.5 top-3.5 pointer-events-none rotate-90" />
              </div>
            </div>

            {/* Category Dropdown filter */}
            <div className="flex flex-col gap-1 min-w-[140px]">
              <span className="text-[10px] text-slate-400 font-extrabold uppercase tracking-wide">Category</span>
              <div className="relative">
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="appearance-none w-full bg-slate-50 border border-slate-200 text-slate-800 text-xs font-bold rounded-xl pl-4 pr-10 py-2.5 outline-none hover:bg-slate-100/70 transition-all duration-200 cursor-pointer focus:border-blue-500"
                >
                  <option value="All Categories">All Categories</option>
                  <option value="Sports & Fitness">Sports & Fitness</option>
                  <option value="Clothing & Accessories">Clothing & Accessories</option>
                  <option value="Home & Kitchen">Home & Kitchen</option>
                  <option value="Beauty">Beauty</option>
                  <option value="Electronics">Electronics</option>
                </select>
                <ArrowPathIcon className="h-3 w-3 text-slate-400 absolute right-3.5 top-3.5 pointer-events-none rotate-90" />
              </div>
            </div>

            {/* Status Dropdown filter */}
            <div className="flex flex-col gap-1 min-w-[130px]">
              <span className="text-[10px] text-slate-400 font-extrabold uppercase tracking-wide">Status</span>
              <div className="relative">
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="appearance-none w-full bg-slate-50 border border-slate-200 text-slate-800 text-xs font-bold rounded-xl pl-4 pr-10 py-2.5 outline-none hover:bg-slate-100/70 transition-all duration-200 cursor-pointer focus:border-blue-500"
                >
                  {statusList.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
                <ArrowPathIcon className="h-3 w-3 text-slate-400 absolute right-3.5 top-3.5 pointer-events-none rotate-90" />
              </div>
            </div>

            {/* Date Range filter */}
            <div className="flex flex-col gap-1 min-w-[130px]">
              <span className="text-[10px] text-slate-400 font-extrabold uppercase tracking-wide">Date Range</span>
              <div className="relative">
                <select
                  value={dateRangeFilter}
                  onChange={(e) => setDateRangeFilter(e.target.value)}
                  className="appearance-none w-full bg-slate-50 border border-slate-200 text-slate-800 text-xs font-bold rounded-xl pl-4 pr-10 py-2.5 outline-none hover:bg-slate-100/70 transition-all duration-200 cursor-pointer focus:border-blue-500"
                >
                  {dateRangeList.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
                <ArrowPathIcon className="h-3 w-3 text-slate-400 absolute right-3.5 top-3.5 pointer-events-none rotate-90" />
              </div>
            </div>

          </div>

          {/* Right Search Input & Global Action Buttons */}
          <div className="flex items-end gap-3 w-full xl:w-auto mt-2 xl:mt-0 justify-between xl:justify-end">
            
            {/* Search Box */}
            <div className="flex flex-col gap-1 w-full sm:w-64">
              <span className="text-[10px] text-slate-400 font-extrabold uppercase tracking-wide">Search Box</span>
              <form onSubmit={handleSearchSubmit} className="relative">
                <Input
                  type="text"
                  placeholder="product name, category, ASIN/SKU"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="!border !border-slate-200 focus:!border-blue-500 bg-slate-50 rounded-xl pl-10 text-xs text-slate-800 placeholder:text-slate-400 focus:bg-white h-[38px]"
                  labelProps={{
                    className: "hidden",
                  }}
                  containerProps={{ className: "min-w-0" }}
                />
                <MagnifyingGlassIcon className="h-4.5 w-4.5 text-slate-400 absolute left-3 top-2.5" />
              </form>
            </div>

            {/* Refresh Report Button */}
            <IconButton
              variant="outlined"
              color="blue-gray"
              onClick={handleRefresh}
              disabled={refreshing}
              title="Refresh Report"
              className="rounded-xl border border-slate-200 shrink-0 bg-slate-50 hover:bg-slate-100/70 h-[38px] w-[38px] flex items-center justify-center"
            >
              <ArrowPathIcon className={`h-4.5 w-4.5 text-slate-600 ${refreshing ? "animate-spin" : ""}`} />
            </IconButton>

            {/* Export Button */}
            <Button
              variant="filled"
              color="blue"
              onClick={handleExportData}
              className="rounded-xl font-extrabold text-xs uppercase h-[38px] flex items-center justify-center gap-1.5 px-4 shadow-sm"
            >
              <ArrowDownTrayIcon className="h-4 w-4" />
              <span>Export</span>
            </Button>
          </div>

        </CardBody>
      </Card>

      {/* ========================================================
          HORIZONTAL NAVIGATION TABS MATRIX
         ======================================================== */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 w-full border-b border-slate-100 flex-wrap">
        <button
          onClick={() => setActiveTab("dashboard")}
          className={`flex items-center gap-2 px-5 py-3 rounded-xl text-xs font-bold transition-all duration-200 shrink-0 ${
            activeTab === "dashboard"
              ? "bg-slate-900 text-white shadow-sm"
              : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
          }`}
        >
          <ChartBarIcon className="h-4.5 w-4.5" />
          <span>SaaS Overview</span>
        </button>

        <button
          onClick={() => setActiveTab("top-selling")}
          className={`flex items-center gap-2 px-5 py-3 rounded-xl text-xs font-bold transition-all duration-200 shrink-0 ${
            activeTab === "top-selling"
              ? "bg-slate-900 text-white shadow-sm"
              : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
          }`}
        >
          <TrophyIcon className="h-4.5 w-4.5" />
          <span>Top Selling Products</span>
        </button>

        <button
          onClick={() => setActiveTab("mapped-categories")}
          className={`flex items-center gap-2 px-5 py-3 rounded-xl text-xs font-bold transition-all duration-200 shrink-0 ${
            activeTab === "mapped-categories"
              ? "bg-slate-900 text-white shadow-sm"
              : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
          }`}
        >
          <CheckCircleIcon className="h-4.5 w-4.5 text-emerald-500" />
          <span>Mapped Categories</span>
          {summary && summary.completed_categories > 0 && (
            <span className={`text-[10px] px-2 py-0.5 rounded-full font-extrabold ${activeTab === "mapped-categories" ? "bg-slate-800 text-emerald-300" : "bg-emerald-50 text-emerald-700"}`}>
              {summary.completed_categories}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("unmapped-categories")}
          className={`flex items-center gap-2 px-5 py-3 rounded-xl text-xs font-bold transition-all duration-200 shrink-0 ${
            activeTab === "unmapped-categories"
              ? "bg-slate-900 text-white shadow-sm"
              : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
          }`}
        >
          <ExclamationTriangleIcon className="h-4.5 w-4.5 text-amber-500" />
          <span>Unmapped Categories</span>
          {summary && summary.pending_categories > 0 && (
            <span className={`text-[10px] px-2 py-0.5 rounded-full font-extrabold ${activeTab === "unmapped-categories" ? "bg-slate-800 text-amber-300" : "bg-amber-50 text-amber-700"}`}>
              {summary.pending_categories}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("unmapped-products")}
          className={`flex items-center gap-2 px-5 py-3 rounded-xl text-xs font-bold transition-all duration-200 shrink-0 ${
            activeTab === "unmapped-products"
              ? "bg-slate-900 text-white shadow-sm"
              : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
          }`}
        >
          <TagIcon className="h-4.5 w-4.5 text-rose-500" />
          <span>Unmapped Products</span>
          {summary && summary.unmapped_products > 0 && (
            <span className={`text-[10px] px-2 py-0.5 rounded-full font-extrabold ${activeTab === "unmapped-products" ? "bg-slate-800 text-rose-300" : "bg-rose-50 text-rose-700"}`}>
              {summary.unmapped_products}
            </span>
          )}
        </button>
      </div>

      {/* Global Error Banner */}
      {error && (
        <div className="bg-rose-50 border-l-4 border-rose-500 text-rose-800 p-4 rounded-xl flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-2">
            <span className="font-bold text-sm">System Error:</span>
            <span className="text-sm">{error}</span>
          </div>
          <IconButton size="sm" variant="text" color="red" onClick={() => setError(null)}>
            <XMarkIcon className="h-5 w-5" />
          </IconButton>
        </div>
      )}

      {/* ========================================================
          EMPTY STATE VIEW FOR PENDING DATA UPLOAD
         ======================================================== */}
      {isPendingUpload ? (
        <div className="flex flex-col items-center justify-center bg-white border border-slate-100 shadow-sm rounded-2xl py-20 px-6 text-center max-w-4xl mx-auto w-full gap-6">
          <div className="h-24 w-24 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
            <InboxIcon className="h-12 w-12" />
          </div>
          <div>
            <Chip
              value="Pending Data Ingestion"
              color="gray"
              className="bg-slate-100 text-slate-600 font-bold rounded-full mb-3"
            />
            <Typography variant="h4" className="text-slate-800 font-bold">
              {marketplaceFilter} Storefront Data Offline
            </Typography>
            <Typography className="text-slate-500 text-sm max-w-md mx-auto mt-2 leading-relaxed">
              Database lookup completed. There are no ingested catalogs or mapping reports for <strong>{marketplaceFilter}</strong>.
              Simulation is disabled. Awaiting upstream automated imports.
            </Typography>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outlined"
              color="blue"
              className="rounded-xl font-bold py-2.5 px-6"
              onClick={() => setMarketplaceFilter("All")}
            >
              Show Available storefronts
            </Button>
            <Button
              variant="gradient"
              color="blue"
              onClick={handleRefresh}
              loading={refreshing}
              className="rounded-xl font-bold py-2.5 px-6"
            >
              Trigger Manual Check
            </Button>
          </div>
        </div>
      ) : (
        <>
          {/* ========================================================
              KPI SUMMARY CARDS GRID
             ======================================================== */}
          {summary && (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
              
              {/* Total Products */}
              <Card className="border border-slate-100/60 shadow-sm rounded-2xl overflow-hidden bg-white hover:-translate-y-0.5 transition-all duration-200">
                <CardBody className="p-5 flex items-center justify-between">
                  <div>
                    <Typography variant="small" className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                      Total Products Catalog
                    </Typography>
                    <Typography variant="h3" className="text-slate-800 font-extrabold tracking-tight mt-1">
                      {Number(summary.total_products).toLocaleString("en-IN")}
                    </Typography>
                    <div className="flex items-center gap-1.5 mt-2">
                      <span className="h-2 w-2 rounded-full bg-blue-500" />
                      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wide">
                        Total database rows
                      </span>
                    </div>
                  </div>
                  <div className="p-3 bg-blue-50/50 rounded-xl border border-blue-100 text-blue-600">
                    <ShoppingBagIcon className="h-6 w-6" />
                  </div>
                </CardBody>
              </Card>

              {/* Mapped Catalog Products */}
              <Card className="border border-slate-100/60 shadow-sm rounded-2xl overflow-hidden bg-white hover:-translate-y-0.5 transition-all duration-200">
                <CardBody className="p-5 flex items-center justify-between">
                  <div>
                    <Typography variant="small" className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                      Mapped Products Rate
                    </Typography>
                    <Typography variant="h3" className="text-slate-800 font-extrabold tracking-tight mt-1">
                      {Number(summary.mapped_products).toLocaleString("en-IN")}
                    </Typography>
                    <div className="flex items-center gap-1 mt-2">
                      <span className="text-emerald-600 font-bold text-xs">
                        {summary.total_products > 0
                          ? ((Number(summary.mapped_products) / Number(summary.total_products)) * 100).toFixed(1)
                          : 0}
                        %
                      </span>
                      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wide">
                        successfully mapped
                      </span>
                    </div>
                  </div>
                  <div className="p-3 bg-emerald-50/50 rounded-xl border border-emerald-100 text-emerald-600">
                    <CheckCircleIcon className="h-6 w-6" />
                  </div>
                </CardBody>
              </Card>

              {/* Out Of Stock Metrics */}
              <Card className="border border-slate-100/60 shadow-sm rounded-2xl overflow-hidden bg-white hover:-translate-y-0.5 transition-all duration-200">
                <CardBody className="p-5 flex items-center justify-between">
                  <div>
                    <Typography variant="small" className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                      Catalog Stock Availability
                    </Typography>
                    <Typography variant="h3" className="text-slate-800 font-extrabold tracking-tight mt-1">
                      {Number(summary.available_products).toLocaleString("en-IN")}
                    </Typography>
                    <div className="flex items-center gap-1 mt-2">
                      <span className="text-slate-500 font-bold text-xs">
                        {Number(summary.out_of_stock_products)} out of stock
                      </span>
                    </div>
                  </div>
                  <div className="p-3 bg-purple-50/50 rounded-xl border border-purple-100 text-purple-600">
                    <ArchiveBoxIcon className="h-6 w-6" />
                  </div>
                </CardBody>
              </Card>

              {/* Avg Selling Price */}
              <Card className="border border-slate-100/60 shadow-sm rounded-2xl overflow-hidden bg-white hover:-translate-y-0.5 transition-all duration-200">
                <CardBody className="p-5 flex items-center justify-between">
                  <div>
                    <Typography variant="small" className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                      Average Selling Price
                    </Typography>
                    <Typography variant="h3" className="text-slate-800 font-extrabold tracking-tight mt-1">
                      ₹{Number(summary.avg_selling_price).toFixed(2)}
                    </Typography>
                    <div className="flex items-center gap-1 mt-2">
                      <span className="text-indigo-600 font-semibold text-xs">
                        {Number(summary.total_brands)} distinct brands
                      </span>
                    </div>
                  </div>
                  <div className="p-3 bg-amber-50/50 rounded-xl border border-amber-100 text-amber-600">
                    <CurrencyRupeeIcon className="h-6 w-6" />
                  </div>
                </CardBody>
              </Card>

            </div>
          )}

          {/* ========================================================
              DASHBOARD TABS VIEW (Overview & Charts)
             ======================================================== */}
          {activeTab === "dashboard" && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* Recharts Pie Chart widget */}
              <Card className="border border-slate-100 shadow-sm rounded-2xl lg:col-span-1 bg-white">
                <CardBody className="p-5">
                  <Typography className="text-slate-800 font-bold text-sm mb-4">
                    Category Mapping Progress
                  </Typography>
                  {categoryCounts && Number(categoryCounts.total_categories) > 0 ? (
                    <div className="h-64 flex flex-col items-center justify-center">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={getPieChartData()}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={80}
                            paddingAngle={5}
                            dataKey="value"
                          >
                            {getPieChartData().map((entry, idx) => (
                              <Cell key={`cell-${idx}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip formatter={(v) => [`${v} categories`, "Count"]} />
                          <Legend verticalAlign="bottom" height={36} iconType="circle" />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <div className="h-64 flex items-center justify-center text-slate-400 text-xs italic">
                      No categories found in registry database.
                    </div>
                  )}
                </CardBody>
              </Card>

              {/* Recharts Stacked Bar Chart */}
              <Card className="border border-slate-100 shadow-sm rounded-2xl lg:col-span-2 bg-white">
                <CardBody className="p-5">
                  <Typography className="text-slate-800 font-bold text-sm mb-4">
                    Catalog Mapping Volume Distribution
                  </Typography>
                  {summary && Number(summary.total_products) > 0 ? (
                    <div className="h-64 flex flex-col justify-center">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={getProductBarData()} layout="vertical" margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                          <XAxis type="number" stroke="#94a3b8" />
                          <YAxis type="category" dataKey="name" stroke="#94a3b8" />
                          <Tooltip formatter={(v) => [`${Number(v).toLocaleString()} items`, "Count"]} />
                          <Legend />
                          <Bar dataKey="Mapped" fill={COLORS.success} stackId="a" radius={[0, 8, 8, 0]} />
                          <Bar dataKey="Unmapped" fill={COLORS.danger} stackId="a" radius={[0, 8, 8, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <div className="h-64 flex items-center justify-center text-slate-400 text-xs italic">
                      No products found in registry database.
                    </div>
                  )}
                </CardBody>
              </Card>

              {/* Marketplace Overview Quick Status Grid */}
              <div className="lg:col-span-3">
                <Card className="border border-slate-100 shadow-sm rounded-2xl bg-white overflow-hidden">
                  <div className="bg-slate-50 px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                    <Typography className="text-slate-800 font-bold text-sm">
                      Marketplace Ingestion Roster & Sync State
                    </Typography>
                    <span className="text-[10px] bg-slate-200/80 text-slate-500 font-bold px-2.5 py-1 rounded-full uppercase tracking-wider">
                      All Channels mapped
                    </span>
                  </div>
                  <CardBody className="p-0">
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[700px] text-left border-collapse">
                        <thead>
                          <tr className="bg-slate-50/40 text-[10px] text-slate-500 font-extrabold uppercase border-b border-slate-100">
                            <th className="py-3.5 px-6">Storefront Marketplace</th>
                            <th className="py-3.5 px-6">Integration Status</th>
                            <th className="py-3.5 px-6">Total Ingested Products</th>
                            <th className="py-3.5 px-6">Mapped Categories</th>
                            <th className="py-3.5 px-6">Avg Price</th>
                            <th className="py-3.5 px-6 text-right">Data Ingest actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 text-sm">
                          {/* Amazon (Real Row) */}
                          <tr className="hover:bg-slate-50/40 transition-colors">
                            <td className="py-4 px-6 font-bold text-slate-900 flex items-center gap-3">
                              <span className="h-3 w-3 rounded-full bg-blue-500 shrink-0" />
                              Amazon
                            </td>
                            <td className="py-4 px-6">
                              <Chip value="Active" color="green" size="sm" className="bg-emerald-50 text-emerald-700 border border-emerald-100 rounded-full font-bold px-2.5 py-0.5 text-[10px]" />
                            </td>
                            <td className="py-4 px-6 font-semibold">
                              {summary && summary.marketplace_name?.toLowerCase() === "amazon" ? Number(summary.total_products).toLocaleString() : "1,612,983"}
                            </td>
                            <td className="py-4 px-6 text-slate-500 font-medium">
                              {summary && summary.marketplace_name?.toLowerCase() === "amazon" ? summary.completed_categories : "488"}
                            </td>
                            <td className="py-4 px-6 font-bold text-slate-900">
                              ₹{summary && summary.marketplace_name?.toLowerCase() === "amazon" ? Number(summary.avg_selling_price).toFixed(2) : "2,808.28"}
                            </td>
                            <td className="py-4 px-6 text-right">
                              <Button size="sm" variant="text" color="blue" onClick={() => setMarketplaceFilter("Amazon")}>
                                Drill down
                              </Button>
                            </td>
                          </tr>

                          {/* Other Simulated/Offline Marketplaces */}
                          {["IndiaMART", "BigBasket", "DMart", "Blinkit", "JioMart", "Flipkart"].map((m) => (
                            <tr key={m} className="hover:bg-slate-50/40 transition-colors text-slate-400">
                              <td className="py-4 px-6 font-semibold flex items-center gap-3">
                                <span className="h-3 w-3 rounded-full bg-slate-300 shrink-0" />
                                {m}
                              </td>
                              <td className="py-4 px-6">
                                <Chip value="Pending Data Upload" color="gray" size="sm" className="bg-slate-100 text-slate-500 rounded-full font-bold px-2.5 py-0.5 text-[10px]" />
                              </td>
                              <td className="py-4 px-6">0</td>
                              <td className="py-4 px-6">—</td>
                              <td className="py-4 px-6">—</td>
                              <td className="py-4 px-6 text-right">
                                <Button size="sm" variant="text" color="gray" onClick={() => setMarketplaceFilter(m)}>
                                  Inspect setup
                                </Button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardBody>
                </Card>
              </div>

              {/* Dashboard Top 5 Products Quick Glance */}
              <div className="lg:col-span-3">
                <Card className="border border-slate-100 shadow-sm rounded-2xl bg-white overflow-hidden">
                  <div className="bg-slate-50 px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                    <Typography className="text-slate-800 font-bold text-sm">
                      High Ranking Products Hotlist
                    </Typography>
                    <Button size="sm" variant="text" color="blue" className="text-xs" onClick={() => setActiveTab("top-selling")}>
                      View all products
                    </Button>
                  </div>
                  <CardBody className="p-0">
                    {loading ? (
                      <div className="flex justify-center py-12">
                        <Spinner className="h-8 w-8 text-blue-500" />
                      </div>
                    ) : topProducts.length === 0 ? (
                      <div className="text-center py-12 text-slate-400 italic">No products found.</div>
                    ) : (
                      <div className="divide-y divide-slate-100">
                        {topProducts.slice(0, 5).map((product, idx) => (
                          <div key={product.product_id || idx} className="p-4 flex items-center justify-between hover:bg-slate-50/30 transition-colors flex-wrap gap-4 text-sm">
                            <div className="flex items-center gap-3 w-full sm:w-2/3">
                              <div className="h-12 w-12 bg-slate-50 border border-slate-100 rounded-lg overflow-hidden shrink-0 flex items-center justify-center">
                                {product.img_url ? (
                                  <img src={product.img_url} alt="" className="h-full w-full object-contain p-1" />
                                ) : (
                                  <ShoppingBagIcon className="h-6 w-6 text-slate-300" />
                                )}
                              </div>
                              <div className="truncate">
                                <Typography className="font-bold text-slate-900 truncate max-w-lg" title={product.product_name}>
                                  {product.product_name}
                                </Typography>
                                <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-500">
                                  <span className="font-semibold text-blue-600">{product.marketplace_name}</span>
                                  <span>•</span>
                                  <span className="truncate max-w-[200px]">{product.category_name}</span>
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center gap-4 ml-auto sm:ml-0">
                              <div className="text-right">
                                <Typography className="font-bold text-slate-900">
                                  {product.price ? `₹${Number(product.price).toLocaleString("en-IN")}` : "—"}
                                </Typography>
                                <Typography className="text-[10px] text-slate-400 font-bold">
                                  Score: {Number(product.ranking_score).toFixed(1)}
                                </Typography>
                              </div>
                              <Button size="sm" variant="outlined" color="blue" onClick={() => openProductDrawer(product)} className="rounded-lg">
                                Specs
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardBody>
                </Card>
              </div>

            </div>
          )}

          {/* ========================================================
              TAB: TOP SELLING PRODUCTS REGISTER GRID
             ======================================================== */}
          {activeTab === "top-selling" && (
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <div>
                  <Typography variant="h5" className="text-slate-800 font-extrabold leading-tight">
                    Top Selling catalog
                  </Typography>
                  <Typography className="text-slate-500 text-xs mt-0.5">
                    Displaying products filtered by ranking parameters
                  </Typography>
                </div>
                <Typography className="text-slate-400 text-xs font-semibold">
                  Found {topProducts.length} items
                </Typography>
              </div>

              {loading ? (
                <div className="flex flex-col items-center justify-center py-20 gap-3 bg-white border rounded-2xl">
                  <Spinner className="h-8 w-8 text-blue-500" />
                  <Typography className="text-xs text-slate-500">Retrieving catalog records…</Typography>
                </div>
              ) : topProducts.length === 0 ? (
                <div className="bg-white border rounded-2xl py-16 text-center text-slate-400 italic text-sm">
                  No matching products found.
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  {topProducts.map((product, idx) => (
                    <Card key={product.product_id || idx} className="border border-slate-100 shadow-sm rounded-xl overflow-hidden hover:shadow-md transition-all duration-200 flex flex-col bg-white">
                      <div className="relative h-44 bg-slate-50/50 flex items-center justify-center border-b border-slate-100">
                        {product.img_url ? (
                          <img src={product.img_url} alt="" className="h-full w-full object-contain p-3" />
                        ) : (
                          <ShoppingBagIcon className="h-12 w-12 text-slate-200" />
                        )}
                        <div className="absolute top-2 left-2 bg-slate-900/80 text-white font-bold text-[10px] px-2 py-0.5 rounded-full backdrop-blur-sm">
                          #{idx + 1}
                        </div>
                        {product.is_best_seller && (
                          <div className="absolute top-2 right-2 bg-orange-500 text-white font-bold text-[9px] px-2 py-0.5 rounded-full flex items-center gap-0.5">
                            <FireIcon className="h-3 w-3" /> Best Seller
                          </div>
                        )}
                      </div>
                      <CardBody className="p-4 flex flex-col flex-1 gap-2 text-xs">
                        <Typography className="text-[10px] text-blue-600 font-bold uppercase tracking-wider truncate">
                          {product.category_name || "Catalog"}
                        </Typography>
                        <Typography className="font-bold text-slate-900 text-sm line-clamp-2 leading-snug" title={product.product_name}>
                          {product.product_name}
                        </Typography>
                        <div className="flex items-center gap-2 mt-auto">
                          <Typography className="font-bold text-slate-900 text-sm">
                            {product.price ? `₹${Number(product.price).toLocaleString("en-IN")}` : "—"}
                          </Typography>
                          {product.list_price && product.list_price > product.price && (
                            <Typography className="text-slate-400 line-through text-[10px]">
                              ₹{Number(product.list_price).toLocaleString("en-IN")}
                            </Typography>
                          )}
                        </div>
                        <div className="flex items-center justify-between border-t border-slate-100 pt-3 mt-1">
                          <StarRating value={product.stars} />
                          <Button size="sm" variant="text" color="blue" onClick={() => openProductDrawer(product)} className="py-1 px-2.5 rounded-lg text-[10px] font-bold">
                            Details
                          </Button>
                        </div>
                      </CardBody>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ========================================================
              TAB: MAPPED CATEGORIES LIST
             ======================================================== */}
          {activeTab === "mapped-categories" && (
            <Card className="border border-slate-100 shadow-sm rounded-2xl bg-white overflow-hidden">
              <div className="bg-slate-50 px-5 py-4 border-b border-slate-100 flex items-center justify-between flex-wrap gap-4">
                <div>
                  <Typography className="text-slate-800 font-bold text-sm">
                    Mapped Category Master Paths
                  </Typography>
                  <Typography className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mt-0.5">
                    Fully reconciled hierarchies
                  </Typography>
                </div>
                <Chip
                  value={`${mappedCategories.length} categories`}
                  color="green"
                  size="sm"
                  className="bg-emerald-50 text-emerald-700 border border-emerald-100 font-bold rounded-full text-[10px] py-1 px-3"
                />
              </div>
              <CardBody className="p-0">
                {loading ? (
                  <div className="flex justify-center py-20">
                    <Spinner className="h-8 w-8 text-blue-500" />
                  </div>
                ) : mappedCategories.length === 0 ? (
                  <div className="text-center py-20 text-slate-400 italic text-sm">
                    No mapped categories found in index.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left min-w-[600px] border-collapse text-sm">
                      <thead>
                        <tr className="bg-slate-50/60 text-[10px] text-slate-500 font-extrabold uppercase border-b border-slate-100">
                          <th className="py-3.5 px-6">Category ID</th>
                          <th className="py-3.5 px-6">Storefront Source</th>
                          <th className="py-3.5 px-6">Level</th>
                          <th className="py-3.5 px-6">Path Tree</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 text-slate-700">
                        {mappedCategories.map((c) => (
                          <tr key={c.id} className="hover:bg-slate-50/30 transition-colors">
                            <td className="py-3.5 px-6 font-semibold text-slate-400 text-xs">
                              #{c.id}
                            </td>
                            <td className="py-3.5 px-6 font-bold text-slate-900 text-xs uppercase">
                              {c.marketplace_name}
                            </td>
                            <td className="py-3.5 px-6 text-xs font-semibold">
                              <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-600 border border-blue-100">
                                L{c.category_level}
                              </span>
                            </td>
                            <td className="py-3.5 px-6 font-medium text-slate-900 text-xs leading-relaxed">
                              {c.category_path}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardBody>
            </Card>
          )}

          {/* ========================================================
              TAB: UNMAPPED CATEGORIES LIST
             ======================================================== */}
          {activeTab === "unmapped-categories" && (
            <Card className="border border-slate-100 shadow-sm rounded-2xl bg-white overflow-hidden">
              <div className="bg-slate-50 px-5 py-4 border-b border-slate-100 flex items-center justify-between flex-wrap gap-4">
                <div>
                  <Typography className="text-slate-800 font-bold text-sm">
                    Unmapped Categories pending reconciliation
                  </Typography>
                  <Typography className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mt-0.5">
                    Exceptions identified by ETL Pipeline
                  </Typography>
                </div>
                <Chip
                  value={`${unmappedCategories.length} issues`}
                  color="amber"
                  size="sm"
                  className="bg-amber-50 text-amber-700 border border-amber-100 font-bold rounded-full text-[10px] py-1 px-3"
                />
              </div>
              <CardBody className="p-0">
                {loading ? (
                  <div className="flex justify-center py-20">
                    <Spinner className="h-8 w-8 text-blue-500" />
                  </div>
                ) : unmappedCategories.length === 0 ? (
                  <div className="text-center py-20 text-slate-400 italic text-sm">
                    No unmapped categories pending.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left min-w-[700px] border-collapse text-sm">
                      <thead>
                        <tr className="bg-slate-50/60 text-[10px] text-slate-500 font-extrabold uppercase border-b border-slate-100">
                          <th className="py-3.5 px-6">Exception ID</th>
                          <th className="py-3.5 px-6">Storefront Source</th>
                          <th className="py-3.5 px-6">Path Tree</th>
                          <th className="py-3.5 px-6">Etl rejection reason</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 text-slate-700">
                        {unmappedCategories.map((c) => (
                          <tr key={c.id} className="hover:bg-slate-50/30 transition-colors">
                            <td className="py-3.5 px-6 font-semibold text-slate-400 text-xs">
                              #{c.category_id || c.id}
                            </td>
                            <td className="py-3.5 px-6 font-bold text-slate-900 text-xs uppercase">
                              {c.marketplace_name}
                            </td>
                            <td className="py-3.5 px-6 font-medium text-slate-900 text-xs leading-relaxed max-w-sm truncate" title={c.category_path}>
                              {c.category_path}
                            </td>
                            <td className="py-3.5 px-6 text-xs">
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-50 text-rose-700 border border-rose-100 font-semibold leading-tight">
                                  <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
                                  {c.reason}
                                </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardBody>
            </Card>
          )}

          {/* ========================================================
              TAB: UNMAPPED PRODUCTS LIST
             ======================================================== */}
          {activeTab === "unmapped-products" && (
            <Card className="border border-slate-100 shadow-sm rounded-2xl bg-white overflow-hidden">
              <div className="bg-slate-50 px-5 py-4 border-b border-slate-100 flex items-center justify-between flex-wrap gap-4">
                <div>
                  <Typography className="text-slate-800 font-bold text-sm">
                    Unmapped catalog items pending mapping
                  </Typography>
                  <Typography className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mt-0.5">
                    Products lacking correct category linkages
                  </Typography>
                </div>
                <Chip
                  value={`${unmappedProducts.length} pending items`}
                  color="red"
                  size="sm"
                  className="bg-rose-50 text-rose-700 border border-rose-100 font-bold rounded-full text-[10px] py-1 px-3"
                />
              </div>
              <CardBody className="p-0">
                {loading ? (
                  <div className="flex justify-center py-20">
                    <Spinner className="h-8 w-8 text-blue-500" />
                  </div>
                ) : unmappedProducts.length === 0 ? (
                  <div className="text-center py-20 text-slate-400 italic text-sm">
                    All catalog items successfully mapped!
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left min-w-[800px] border-collapse text-sm">
                      <thead>
                        <tr className="bg-slate-50/60 text-[10px] text-slate-500 font-extrabold uppercase border-b border-slate-100">
                          <th className="py-3.5 px-6">ID / ASIN</th>
                          <th className="py-3.5 px-6">Storefront</th>
                          <th className="py-3.5 px-6">Product Details</th>
                          <th className="py-3.5 px-6 text-right">Rejection reason</th>
                          <th className="py-3.5 px-6 text-right">Mapping Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 text-slate-700">
                        {unmappedProducts.map((p) => (
                          <tr key={p.id} className="hover:bg-slate-50/30 transition-colors">
                            <td className="py-3.5 px-6 font-semibold text-slate-500 text-xs">
                              {p.asin || `#${p.product_id}`}
                            </td>
                            <td className="py-3.5 px-6 font-bold text-slate-900 text-xs uppercase">
                              {p.marketplace_name}
                            </td>
                            <td className="py-3.5 px-6 max-w-md">
                              <div className="flex flex-col">
                                <span className="font-bold text-slate-950 truncate max-w-sm" title={p.product_name}>
                                  {p.product_name}
                                </span>
                                <span className="text-[10px] text-slate-400 mt-0.5">
                                  Brand: {p.brand || "Unknown"} | Category: {p.category_name || "Uncategorized"}
                                </span>
                              </div>
                            </td>
                            <td className="py-3.5 px-6 text-xs text-center">
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 font-semibold border border-slate-200">
                                <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
                                {p.reason}
                              </span>
                            </td>
                            <td className="py-3.5 px-6 text-right">
                              <Button size="sm" variant="text" color="blue" onClick={() => openProductDrawer(p)} className="rounded-lg text-xs py-1 px-3">
                                specs
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardBody>
            </Card>
          )}

        </>
      )}

      {/* ========================================================
          SLIDING RIGHT PRODUCT SPECIFICATIONS DRAWER WIDGET
         ======================================================== */}
      {isDrawerOpen && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          <div
            className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity duration-300 ease-out"
            onClick={() => setIsDrawerOpen(false)}
          />

          <div className="fixed inset-y-0 right-0 max-w-full flex pl-10 z-50">
            <div className="w-screen max-w-lg bg-white shadow-2xl flex flex-col justify-between border-l border-slate-100">
              
              <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6 text-slate-800">
                
                <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                  <div>
                    <Typography className="text-slate-800 font-extrabold text-lg">
                      Technical Specifications
                    </Typography>
                    <Typography className="text-slate-400 text-xs mt-0.5 uppercase font-bold tracking-wider">
                      Reconciliation Audit Details
                    </Typography>
                  </div>
                  <IconButton
                    variant="text"
                    color="blue-gray"
                    onClick={() => setIsDrawerOpen(false)}
                    className="rounded-full hover:rotate-90 transition-transform duration-200"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </IconButton>
                </div>

                {drawerLoading ? (
                  <div className="flex flex-col items-center justify-center flex-1 py-32 gap-3">
                    <Spinner className="h-10 w-10 text-blue-500" />
                    <Typography className="text-slate-400 text-xs">Fetching deep properties from database…</Typography>
                  </div>
                ) : selectedProduct ? (
                  <div className="flex flex-col gap-5 text-sm">
                    
                    <div className="h-64 bg-slate-50 rounded-2xl overflow-hidden border border-slate-100 flex items-center justify-center relative">
                      {selectedProduct.imgUrl ? (
                        <img
                          src={selectedProduct.imgUrl}
                          alt=""
                          className="h-full w-full object-contain p-4"
                        />
                      ) : (
                        <ShoppingBagIcon className="h-20 w-20 text-slate-200" />
                      )}
                      
                      <span className="absolute bottom-3 left-3 bg-[#0f172a] text-white font-bold text-[10px] uppercase tracking-wider py-1 px-2.5 rounded-lg shadow-md">
                        {selectedProduct.marketplace_name || "Amazon"}
                      </span>
                    </div>

                    <div>
                      <Typography className="font-extrabold text-slate-900 text-base leading-snug">
                        {selectedProduct.title || selectedProduct.product_name}
                      </Typography>
                      {selectedProduct.brand && (
                        <Typography className="text-slate-500 text-xs font-semibold mt-1">
                          Brand/Manufacturer: <span className="text-slate-800 font-bold">{selectedProduct.brand}</span>
                        </Typography>
                      )}
                    </div>

                    <div className="h-px bg-slate-100" />

                    <div className="grid grid-cols-2 gap-4">
                      
                      <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100/60 relative group">
                        <Typography className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                          Catalog Unique ID
                        </Typography>
                        <Typography className="font-bold text-slate-900 mt-0.5 truncate pr-8">
                          {selectedProduct.asin || `#${selectedProduct.id}`}
                        </Typography>
                        <IconButton
                          size="sm"
                          variant="text"
                          className="absolute right-2 top-2 rounded-lg"
                          onClick={() => handleCopyToClipboard(selectedProduct.asin || selectedProduct.id)}
                        >
                          {copySuccess ? (
                            <CheckIcon className="h-4 w-4 text-emerald-600" />
                          ) : (
                            <ClipboardIcon className="h-4 w-4 text-slate-400" />
                          )}
                        </IconButton>
                      </div>

                      <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100/60">
                        <Typography className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                          Bought Velocity
                        </Typography>
                        <Typography className="font-bold text-slate-900 mt-0.5">
                          {selectedProduct.boughtInLastMonth > 0
                            ? `${Number(selectedProduct.boughtInLastMonth).toLocaleString()}+ bought`
                            : "0 bought last month"}
                        </Typography>
                      </div>

                      <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100/60">
                        <Typography className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                          Customer Reviews
                        </Typography>
                        <div className="mt-1 flex items-center gap-1.5">
                          <StarRating value={selectedProduct.stars} />
                          <span className="text-slate-400 font-semibold text-xs">
                            ({Number(selectedProduct.reviews || 0).toLocaleString()})
                          </span>
                        </div>
                      </div>

                      <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100/60">
                        <Typography className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                          Display Sell Price
                        </Typography>
                        <div className="flex items-center gap-2 mt-0.5">
                          <Typography className="font-black text-slate-900 text-sm">
                            {selectedProduct.price ? `₹${Number(selectedProduct.price).toLocaleString("en-IN")}` : "—"}
                          </Typography>
                          {selectedProduct.listPrice && selectedProduct.listPrice > selectedProduct.price && (
                            <Typography className="text-slate-400 line-through text-[10px]">
                              ₹{Number(selectedProduct.listPrice).toLocaleString("en-IN")}
                            </Typography>
                          )}
                        </div>
                      </div>

                    </div>

                    <div className="h-px bg-slate-100" />

                    <div>
                      <Typography className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                        Reconciled Category Hierarchy
                      </Typography>
                      <Typography className="font-semibold text-slate-800 mt-1.5 leading-relaxed bg-slate-50 p-3 rounded-xl border border-slate-100/60 text-xs">
                        {selectedProduct.categoryName || "Uncategorized"}
                      </Typography>
                    </div>

                    {selectedProduct.availability && (
                      <div>
                        <Typography className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                          Stock Availability Status
                        </Typography>
                        <Typography className="font-semibold text-slate-900 mt-1">
                          {selectedProduct.availability}
                        </Typography>
                      </div>
                    )}

                    {selectedProduct.description && (
                      <div>
                        <Typography className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                          Catalog Description Excerpt
                        </Typography>
                        <div className="text-slate-600 text-xs leading-relaxed max-h-36 overflow-y-auto mt-1.5 p-3.5 bg-slate-50/50 rounded-xl border border-slate-100/50">
                          {selectedProduct.description}
                        </div>
                      </div>
                    )}

                  </div>
                ) : (
                  <div className="text-center py-20 text-slate-400 italic text-sm">
                    No specifications data loaded.
                  </div>
                )}

              </div>

              {selectedProduct && (
                <div className="bg-slate-50 p-4 border-t border-slate-100 flex gap-3">
                  <Button
                    variant="outlined"
                    color="blue-gray"
                    onClick={() => setIsDrawerOpen(false)}
                    className="flex-1 rounded-xl py-3 font-bold"
                  >
                    Close Specs
                  </Button>
                  {selectedProduct.productUrl && (
                    <Button
                      variant="filled"
                      color="blue"
                      className="flex-1 flex items-center justify-center gap-1.5 rounded-xl py-3 font-bold shadow-md shadow-blue-500/10"
                      onClick={() => window.open(selectedProduct.productUrl, "_blank")}
                    >
                      <ArrowTopRightOnSquareIcon className="h-4.5 w-4.5" />
                      <span>Direct Storefront Link</span>
                    </Button>
                  )}
                </div>
              )}

            </div>
          </div>
        </div>
      )}

    </div>
  );
}
