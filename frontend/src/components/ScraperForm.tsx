"use client";
import React, { useState } from "react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export default function SignupForm() {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    usn: "",
    range: "",
    url: "",
    is_reval: false,
  });
  const [errors, setErrors] = useState({
    usn: "",
    range: "",
    url: "",
  });
  const [alert, setAlert] = useState({
    type: "",
    message: "",
  });

  const validateUSN = (usn: string) => {
    const usnRegex = /^\d{1}[A-Za-z]{2}\d{2}[A-Za-z]{2,3}$/;
    return usnRegex.test(usn);
  };

  const validateRange = (range: string) => {
    const rangeRegex = /^\d{1,3}([-,]\d{1,3})*$/;
    return rangeRegex.test(range);
  };

  const validateURL = (url: string) => {
    const urlRegex = /^https:\/\/results\.vtu\.ac\.in\/[a-zA-Z0-9]+\/index\.php$/;
    return urlRegex.test(url);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { id, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [id]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAlert({ type: "", message: "" });

    const newErrors = {
      usn: validateUSN(formData.usn) ? "" : "Invalid USN format (e.g., 2AG21CS or 2AG21CS001)",
      range: validateRange(formData.range) ? "" : "Invalid Range format (e.g., 1-60)",
      url: validateURL(formData.url) ? "" : "Invalid URL format (e.g., https://results.vtu.ac.in/DJcbcs25/index.php)",
    };

    setErrors(newErrors);

    if (Object.values(newErrors).some((error) => error !== "")) {
      setLoading(false);
      return;
    }

    try {
      const response = await fetch("https://aitmeduinsight.up.railway.app/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      if (
        response.headers
          .get("content-type")
          ?.includes("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
      ) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "VTU_Results.xlsx";
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);

        setAlert({
          type: "success",
          message: "Results downloaded successfully!",
        });
      } else {
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || data.message || `Request failed: ${response.status}`);
        }
        setAlert({
          type: "success",
          message: data.message || "Request processed successfully!",
        });
      }
    } catch (error) {
      let errorMessage = "An error occurred while processing your request";

      if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
        errorMessage = "Network error: Could not connect to the server. Please try again.";
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }

      setAlert({
        type: "error",
        message: errorMessage,
      });

      console.error("Submission error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="text-center shadow-input mx-auto w-full max-w-sm rounded-none bg-white p-4 md:rounded-2xl md:p-8 dark:bg-black">
      {alert.message && (
        <div
          className={`mb-4 p-4 rounded ${
            alert.type === "success" ? "bg-green-200 text-green-800" : "bg-red-200 text-red-800"
          }`}
        >
          {alert.message}
        </div>
      )}

      <h2 className="text-2xl font-extrabold text-neutral-800 dark:text-neutral-200">
        Welcome to Edu Insight
      </h2>

      <p className="mt-2 max-w-sm text-sm font-medium text-gray-500 dark:text-neutral-300">
        Fill the form to start the automate process
      </p>

      <form className="my-8 mt-32 text-left" onSubmit={handleSubmit}>
        <div className="flex flex-col space-y-2 md:flex-row md:space-y-0 md:space-x-2">
          <LabelInputContainer className="mb-4">
            <Label htmlFor="usn">USN</Label>
            <Input
              id="usn"
              placeholder="2AG21CS"
              type="text"
              value={formData.usn}
              onChange={handleChange}
              maxLength={10}
            />
            {errors.usn && <p className="text-red-500 text-sm">{errors.usn}</p>}
          </LabelInputContainer>
          <LabelInputContainer className="mb-4">
            <Label htmlFor="range">Range</Label>
            <Input
              id="range"
              placeholder="1-60"
              type="text"
              value={formData.range}
              onChange={handleChange}
            />
            {errors.range && <p className="text-red-500 text-sm">{errors.range}</p>}
          </LabelInputContainer>
        </div>
        <LabelInputContainer className="mb-8">
          <Label htmlFor="url">Result URL</Label>
          <Input
            id="url"
            placeholder="https://results.vtu.ac.in/DJcbcs25/index.php"
            type="text"
            value={formData.url}
            onChange={handleChange}
          />
          {errors.url && <p className="text-red-500 text-sm">{errors.url}</p>}
        </LabelInputContainer>

        {loading ? (
          <div className="group/btn relative flex h-12 w-full rounded-md bg-gradient-to-br from-black to-neutral-600 font-medium text-white shadow-[0px_1px_0px_0px_#ffffff40_inset,0px_-1px_0px_0px_#ffffff40_inset] dark:bg-zinc-800 dark:from-zinc-900 dark:to-zinc-900 dark:shadow-[0px_1px_0px_0px_#27272a_inset,0px_-1px_0px_0px_#27272a_inset] cursor-pointer items-center justify-center">
            <div className="h-6 w-6 border-4 border-t-4 border-gray-200 rounded-full animate-spin"></div>
            <span className="ml-2">Processing...</span>
          </div>
        ) : (
          <button
            className="group/btn relative block h-12 w-full rounded-md bg-gradient-to-br from-black to-neutral-600 font-medium text-white shadow-[0px_1px_0px_0px_#ffffff40_inset,0px_-1px_0px_0px_#ffffff40_inset] dark:bg-zinc-800 dark:from-zinc-900 dark:to-zinc-900 dark:shadow-[0px_1px_0px_0px_#27272a_inset,0px_-1px_0px_0px_#27272a_inset] cursor-pointer"
            type="submit"
            disabled={loading}
          >
            <i className="ph ph-spinner-gap mr-2"></i>Start the automate process
            <BottomGradient />
          </button>
        )}
        <div className="my-8 h-[1px] w-full bg-gradient-to-r from-transparent via-neutral-300 to-transparent dark:via-neutral-700" />
        <p className="mt-2 max-w-sm text-[12px] text-center font-medium text-gray-500 dark:text-neutral-300">
          Once the process is finished, your excel file <br />will be ready to download
        </p>
      </form>
    </div>
  );
}

const BottomGradient = () => {
  return (
    <>
      <span className="absolute inset-x-0 -bottom-px block h-px w-full bg-gradient-to-r from-transparent via-cyan-500 to-transparent opacity-0 transition duration-500 group-hover/btn:opacity-100" />
      <span className="absolute inset-x-10 -rgba(255, 255, 255, 0.8)bottom-px mx-auto block h-px w-1/2 bg-gradient-to-r from-transparent via-indigo-500 to-transparent opacity-0 blur-sm transition duration-500 group-hover/btn:opacity-100" />
    </>
  );
};

const LabelInputContainer = ({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) => {
  return <div className={cn("flex w-full flex-col space-y-2", className)}>{children}</div>;
};