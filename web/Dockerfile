# Use Node.js LTS version
FROM node:16

# Set working directory inside the container
WORKDIR /app

# Install dependencies only when needed
COPY package*.json ./
RUN npm install

# Copy the rest of the application files (optional for development)
COPY . .

# Expose the development port
EXPOSE 3000

# Default command to run the development server
CMD ["npm", "run", "serve", "--", "--host", "0.0.0.0", "--port", "3000"]
