# Multi-stage Docker build for OmicsIntegrationSuite
# Contains all necessary bioinformatics tools

# Stage 1: Base image with system dependencies
FROM ubuntu:22.04 AS base

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Update and install system dependencies
RUN apt-get update && apt-get install -y \
    # Basic tools
    wget \
    curl \
    git \
    build-essential \
    cmake \
    pkg-config \
    # Python and pip
    python3.10 \
    python3-pip \
    python3-dev \
    # Libraries for bioinformatics tools
    libz-dev \
    libbz2-dev \
    liblzma-dev \
    libncurses5-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libffi-dev \
    # Additional utilities
    unzip \
    pigz \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Stage 2: Install bioinformatics tools
FROM base AS biotools

# Set working directory for tool installation
WORKDIR /tmp

# Install samtools (v1.17)
RUN wget https://github.com/samtools/samtools/releases/download/1.17/samtools-1.17.tar.bz2 && \
    tar -xjf samtools-1.17.tar.bz2 && \
    cd samtools-1.17 && \
    ./configure --prefix=/usr/local && \
    make && \
    make install && \
    cd .. && \
    rm -rf samtools-1.17*

# Install bcftools (v1.17)
RUN wget https://github.com/samtools/bcftools/releases/download/1.17/bcftools-1.17.tar.bz2 && \
    tar -xjf bcftools-1.17.tar.bz2 && \
    cd bcftools-1.17 && \
    ./configure --prefix=/usr/local && \
    make && \
    make install && \
    cd .. && \
    rm -rf bcftools-1.17*

# Install htslib (v1.17) - required for tabix and bgzip
RUN wget https://github.com/samtools/htslib/releases/download/1.17/htslib-1.17.tar.bz2 && \
    tar -xjf htslib-1.17.tar.bz2 && \
    cd htslib-1.17 && \
    ./configure --prefix=/usr/local && \
    make && \
    make install && \
    cd .. && \
    rm -rf htslib-1.17*

# Install fastp (v0.23.4)
RUN wget http://opengene.org/fastp/fastp.0.23.4 && \
    chmod +x fastp.0.23.4 && \
    mv fastp.0.23.4 /usr/local/bin/fastp

# Install BWA-MEM2 (v2.2.1)
RUN wget https://github.com/bwa-mem2/bwa-mem2/releases/download/v2.2.1/bwa-mem2-2.2.1_x64-linux.tar.bz2 && \
    tar -xjf bwa-mem2-2.2.1_x64-linux.tar.bz2 && \
    cp bwa-mem2-2.2.1_x64-linux/bwa-mem2* /usr/local/bin/ && \
    rm -rf bwa-mem2-2.2.1_x64-linux*

# Install Minimap2 (v2.26)
RUN wget https://github.com/lh3/minimap2/releases/download/v2.26/minimap2-2.26_x64-linux.tar.bz2 && \
    tar -xjf minimap2-2.26_x64-linux.tar.bz2 && \
    cp minimap2-2.26_x64-linux/minimap2 /usr/local/bin/ && \
    rm -rf minimap2-2.26_x64-linux*

# Install FastQC (v0.12.1)
RUN apt-get update && apt-get install -y default-jre && \
    wget https://www.bioinformatics.babraham.ac.uk/projects/fastqc/fastqc_v0.12.1.zip && \
    unzip fastqc_v0.12.1.zip && \
    chmod +x FastQC/fastqc && \
    ln -s /tmp/FastQC/fastqc /usr/local/bin/fastqc && \
    rm fastqc_v0.12.1.zip

# Stage 3: Final image with Python dependencies
FROM biotools AS final

# Set working directory
WORKDIR /app

# Copy requirements file first for better caching
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the OmicsIntegrationSuite code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app:$PYTHONPATH
ENV PATH=/usr/local/bin:$PATH

# Create directories for input/output
RUN mkdir -p /data/input /data/output /data/reference

# Set up entry point
ENTRYPOINT ["python", "-m", "modules.genomics.genomics_processor"]

# Default command (can be overridden)
CMD ["--help"]