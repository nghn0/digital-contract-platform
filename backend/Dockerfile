FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --production

# Copy the rest of the application code
COPY . .

# Expose the API port
EXPOSE 5001

# Command to run the Express server
CMD ["node", "server.js"]
