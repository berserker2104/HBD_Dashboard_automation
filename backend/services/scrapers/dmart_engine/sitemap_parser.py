import logging
import xml.etree.ElementTree as ET
from urllib.request import urlopen, Request
from typing import List

logger = logging.getLogger(__name__)

class SitemapParser:
    SITEMAP_URL = "https://www.dmart.in/sitemap/products.xml"

    @staticmethod
    def fetch_product_urls(limit: int = 0) -> List[str]:
        """
        Fetches the DMart products sitemap and extracts all <loc> URLs.
        
        Args:
            limit: Maximum number of URLs to return (0 for all).
            
        Returns:
            List of product URL strings.
        """
        logger.info(f"Fetching sitemap from {SitemapParser.SITEMAP_URL}")
        req = Request(SitemapParser.SITEMAP_URL, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        
        try:
            with urlopen(req, timeout=30) as response:
                tree = ET.parse(response)
                root = tree.getroot()
                
                # XML namespace handling
                ns = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                
                urls = []
                for url in root.findall('sitemap:url/sitemap:loc', ns):
                    urls.append(url.text)
                    if limit > 0 and len(urls) >= limit:
                        break
                        
                logger.info(f"Extracted {len(urls)} URLs from sitemap.")
                return urls
        except Exception as e:
            logger.error(f"Failed to fetch or parse sitemap: {e}")
            return []
