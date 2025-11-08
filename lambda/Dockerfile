FROM public.ecr.aws/lambda/python:3.12

# Install Playwright and dependencies
RUN pip install playwright beautifulsoup4 soupsieve supabase httpx --no-cache-dir
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy function code
COPY lambda_function.py scraper_utils.py ${LAMBDA_TASK_ROOT}/

CMD ["lambda_function.lambda_handler"]
