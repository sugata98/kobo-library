"use client";

import { useState, useEffect } from "react";
import BookList from "@/components/BookList";
import { Search, BookOpen, FileText } from "lucide-react";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
} from "@/components/ui/input-group";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BRANDING } from "@/lib/branding";
import { getBooks } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

export default function Home() {
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<"book" | "article">("book");
  const [bookCount, setBookCount] = useState<number>(0);
  const [articleCount, setArticleCount] = useState<number>(0);

  // Fetch counts for books and articles
  useEffect(() => {
    const fetchCounts = async () => {
      try {
        // Fetch book count
        const bookResponse = await getBooks(1, 1, undefined, "book");
        setBookCount(bookResponse.pagination?.total || 0);

        // Fetch article count
        const articleResponse = await getBooks(1, 1, undefined, "article");
        setArticleCount(articleResponse.pagination?.total || 0);
      } catch (error) {
        console.error("Failed to fetch counts:", error);
      }
    };

    fetchCounts();
  }, []);

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchQuery(searchQuery);
    }, 300); // 300ms delay

    return () => clearTimeout(timer);
  }, [searchQuery]);

  return (
    <main className="min-h-screen bg-background text-foreground">
      {/* Main Content */}
      <div className="px-4 sm:px-8 lg:px-24 py-6">
        <Tabs
          defaultValue="book"
          value={activeTab}
          onValueChange={(value: string) =>
            setActiveTab(value as "book" | "article")
          }
          className="w-full"
        >
          {/* Tabs with Search Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <TabsList>
              <TabsTrigger value="book" className="gap-2">
                <BookOpen className="h-4 w-4" />
                Books
                <Badge variant="secondary" className="ml-1 px-1.5 py-0 text-xs">
                  {bookCount}
                </Badge>
              </TabsTrigger>
              <TabsTrigger value="article" className="gap-2">
                <FileText className="h-4 w-4" />
                Articles
                <Badge variant="secondary" className="ml-1 px-1.5 py-0 text-xs">
                  {articleCount}
                </Badge>
              </TabsTrigger>
            </TabsList>

            {/* Search Bar - inline with tabs */}
            <div className="w-full sm:w-auto sm:max-w-sm">
              <InputGroup>
                <InputGroupAddon>
                  <Search />
                </InputGroupAddon>
                <InputGroupInput
                  type="text"
                  placeholder={BRANDING.ui.searchPlaceholder}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </InputGroup>
            </div>
          </div>

          <TabsContent value="book" className="mt-0">
            <BookList searchQuery={debouncedSearchQuery} contentType="book" />
          </TabsContent>

          <TabsContent value="article" className="mt-0">
            <BookList
              searchQuery={debouncedSearchQuery}
              contentType="article"
            />
          </TabsContent>
        </Tabs>
      </div>
    </main>
  );
}
