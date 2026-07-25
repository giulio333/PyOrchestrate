# Usa l'immagine di base Node.js
FROM node:20

# Imposta la directory di lavoro nel container
WORKDIR /app

# Copia i file dalla directory corrente del host alla directory di lavoro nel container
COPY . .

# Espone la porta che l'app utilizzerà
#EXPOSE 7891

# Installa le dipendenze
RUN npm install