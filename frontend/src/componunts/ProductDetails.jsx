import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Card,
  CardBody,
  Typography,
  Button,
  Spinner,
  Chip,
} from "@material-tailwind/react";
import {
  StarIcon,
  FireIcon,
  ArrowLeftIcon,
  ArrowTopRightOnSquareIcon,
  ShoppingBagIcon,
} from "@heroicons/react/24/solid";
import api from "../utils/Api";

const InfoRow = ({ label, value, valueClass = "" }) => (
  <div className="flex items-start gap-3 py-3 border-b border-slate-100 last:border-0">
    <Typography variant="small" className="text-slate-500 font-semibold w-40 shrink-0">
      {label}
    </Typography>
    <Typography variant="small" className={`text-slate-800 font-medium flex-1 ${valueClass}`}>
      {value ?? "—"}
    </Typography>
  </div>
);

export default function ProductDetails() {
  const { asin }    = useParams();
  const navigate    = useNavigate();
  const [product, setProduct]   = useState(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);

  useEffect(() => {
    if (!asin) return;
    const fetchProduct = async () => {
      try {
        const res = await api.get(`/product-report/products/${asin}`);
        setProduct(res.data?.data || null);
      } catch (e) {
        if (e.response?.status === 404) {
          setError(`No product found in amazon_products for ASIN: ${asin}`);
        } else {
          setError("Failed to load product details.");
        }
      } finally {
        setLoading(false);
      }
    };
    fetchProduct();
  }, [asin]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-4">
        <Spinner className="h-10 w-10 text-blue-500" />
        <Typography className="text-slate-500">Loading product details…</Typography>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="mt-8 px-4">
        <Button
          variant="text"
          className="flex items-center gap-2 text-slate-600 mb-6"
          onClick={() => navigate(-1)}
        >
          <ArrowLeftIcon className="h-4 w-4" /> Back
        </Button>
        <div className="flex flex-col items-center justify-center py-24 gap-3">
          <ShoppingBagIcon className="h-14 w-14 text-slate-200" />
          <Typography variant="h6" className="text-slate-500 font-semibold">
            {error || "Product not found"}
          </Typography>
          <Typography variant="small" className="text-slate-400">
            ASIN: {asin}
          </Typography>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-8 mb-12 px-4 xl:px-8 max-w-5xl mx-auto">
      {/* Back button */}
      <Button
        variant="text"
        className="flex items-center gap-2 text-slate-600 mb-6 pl-0"
        onClick={() => navigate(-1)}
      >
        <ArrowLeftIcon className="h-4 w-4" /> Back to Top Products
      </Button>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">

        {/* ── Left: Image + badges ── */}
        <div className="lg:col-span-2">
          <Card className="border border-slate-100 shadow-sm rounded-xl overflow-hidden">
            <div className="bg-slate-50 flex items-center justify-center h-72 p-4 relative">
              {product.imgUrl ? (
                <img
                  src={product.imgUrl}
                  alt={product.title}
                  className="h-full w-full object-contain"
                  onError={(e) => { e.target.style.display = "none"; }}
                />
              ) : (
                <ShoppingBagIcon className="h-24 w-24 text-slate-200" />
              )}

              {/* Badges */}
              <div className="absolute top-3 right-3 flex flex-col gap-1">
                {product.isBestSeller && (
                  <span className="flex items-center gap-1 bg-orange-500 text-white text-xs font-bold px-2 py-1 rounded-full">
                    <FireIcon className="h-3.5 w-3.5" /> Best Seller
                  </span>
                )}
              </div>
            </div>

            <CardBody className="p-4 flex flex-col gap-3">
              {/* Stars */}
              <div className="flex items-center gap-2">
                {product.stars ? (
                  <span className="flex items-center gap-1 text-amber-500 font-bold text-lg">
                    <StarIcon className="h-5 w-5" />
                    {Number(product.stars).toFixed(1)}
                  </span>
                ) : null}
                {product.reviews > 0 && (
                  <Typography variant="small" className="text-slate-500">
                    ({Number(product.reviews).toLocaleString("en-IN")} reviews)
                  </Typography>
                )}
              </div>

              {/* Price */}
              <div className="flex items-center gap-3 flex-wrap">
                {product.price != null && (
                  <Typography className="font-bold text-slate-900 text-2xl">
                    ₹{Number(product.price).toLocaleString("en-IN")}
                  </Typography>
                )}
                {product.listPrice && product.listPrice > product.price && (
                  <Typography className="text-slate-400 text-base line-through">
                    ₹{Number(product.listPrice).toLocaleString("en-IN")}
                  </Typography>
                )}
              </div>

              {/* Bought last month */}
              {product.boughtInLastMonth > 0 && (
                <Typography variant="small" className="text-emerald-600 font-semibold">
                  {Number(product.boughtInLastMonth).toLocaleString("en-IN")}+ bought last month
                </Typography>
              )}

              {/* Open on Amazon */}
              {product.productUrl && (
                <Button
                  color="orange"
                  className="flex items-center justify-center gap-2 w-full mt-2"
                  onClick={() => window.open(product.productUrl, "_blank")}
                >
                  <ArrowTopRightOnSquareIcon className="h-4 w-4" />
                  Open Source
                </Button>
              )}
            </CardBody>
          </Card>
        </div>

        {/* ── Right: Details ── */}
        <div className="lg:col-span-3">
          <Card className="border border-slate-100 shadow-sm rounded-xl overflow-hidden">
            <div className="p-5 bg-slate-50 border-b border-slate-100">
              <Typography variant="h5" className="font-bold text-slate-800 leading-snug">
                {product.title}
              </Typography>
            </div>

            <CardBody className="p-5">
              <InfoRow label="ASIN"         value={product.asin} valueClass="font-mono text-blue-600" />
              <InfoRow label="Category"     value={product.categoryName} />
              <InfoRow
                label="Price"
                value={product.price != null ? `₹${Number(product.price).toLocaleString("en-IN")}` : null}
              />
              <InfoRow
                label="MRP (List Price)"
                value={product.listPrice ? `₹${Number(product.listPrice).toLocaleString("en-IN")}` : null}
              />
              <InfoRow
                label="Star Rating"
                value={product.stars ? `${Number(product.stars).toFixed(1)} / 5` : null}
              />
              <InfoRow
                label="Reviews"
                value={product.reviews ? Number(product.reviews).toLocaleString("en-IN") : null}
              />
              <InfoRow
                label="Best Seller"
                value={
                  product.isBestSeller ? (
                    <Chip value="Yes" color="orange" size="sm" className="w-fit" />
                  ) : (
                    <Chip value="No" color="gray" size="sm" className="w-fit" />
                  )
                }
              />
              <InfoRow
                label="Bought Last Month"
                value={
                  product.boughtInLastMonth > 0
                    ? `${Number(product.boughtInLastMonth).toLocaleString("en-IN")}+`
                    : null
                }
              />
              <InfoRow
                label="Product URL"
                value={
                  product.productUrl ? (
                    <a
                      href={product.productUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-500 hover:text-blue-700 underline break-all"
                    >
                      {product.productUrl.length > 60
                        ? product.productUrl.slice(0, 60) + "…"
                        : product.productUrl}
                    </a>
                  ) : null
                }
              />
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}
