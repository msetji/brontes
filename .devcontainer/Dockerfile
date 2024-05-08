FROM python:3.11-buster

# Install the tools
RUN apt-get update && \
  apt-get install -y sudo \
  curl \
  locales \
  zsh \
  wget \
  vim \
  fonts-powerline && \
  locale-gen en_US.UTF-8 && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# Install Python packages as root
RUN pip install poetry==1.4.2 \
    && poetry config virtualenvs.create false \
    && poetry self add poetry-dotenv-plugin

# Create user with specified UID/GID and add to sudoers
ARG USERNAME=brontes
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    #
    # [Optional] Add sudo support. Omit if you don't need to install software after connecting.
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Switch to non-root user
USER $USERNAME

# Set environment variables
ENV SHELL=/bin/bash \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache


CMD ["sleep", "infinity"]
