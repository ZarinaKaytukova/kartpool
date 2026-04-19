// stores/static/js/favorites.js

class FavoritesManager {
    constructor() {
        this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        this.isAuthenticated = document.body.dataset.userAuthenticated === 'true';
        this.init();
    }

    init() {
        this.bindGlobalButtons();
        this.loadFavoritesForMap();
        this.renderFavoritesList();
    }

    // Привязка обработчиков к динамическим кнопкам
    bindGlobalButtons() {
        document.addEventListener('click', async (e) => {
            const favoriteBtn = e.target.closest('.favorite-btn');
            if (!favoriteBtn) return;

            e.preventDefault();
            const storeId = favoriteBtn.dataset.storeId;
            
            if (!this.isAuthenticated) {
                alert('Пожалуйста, войдите в систему');
                window.location.href = '/login/';
                return;
            }

            // Определяем текущее состояние (в избранном или нет)
            const isFavorite = favoriteBtn.classList.contains('active');
            
            if (isFavorite) {
                await this.removeFromFavorites(storeId, favoriteBtn);
            } else {
                await this.addToFavorites(storeId, favoriteBtn);
            }
        });
    }

    async addToFavorites(storeId, button) {
        try {
            const response = await fetch('/api/favorites/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken,
                },
                body: JSON.stringify({ store_id: parseInt(storeId) })
            });

            if (response.status === 201) {
                this.updateButtonState(button, true);
                const data = await response.json();
                console.log('Added to favorites:', data);
                
                // Показываем уведомление (можно заменить на toast)
                this.showNotification('Магазин добавлен в избранное ❤️', 'success');
            } else if (response.status === 409) {
                this.showNotification('Этот магазин уже в избранном', 'info');
                this.updateButtonState(button, true);
            } else {
                throw new Error(`HTTP error: ${response.status}`);
            }
        } catch (error) {
            console.error('Error adding to favorites:', error);
            this.showNotification('Ошибка при добавлении в избранное', 'error');
        }
    }

    async removeFromFavorites(storeId, button) {
        // Сначала нужно получить ID записи Favorite
        try {
            const response = await fetch('/api/favorites/');
            const favorites = await response.json();
            
            const favorite = favorites.find(f => f.store_detail.id === parseInt(storeId));
            
            if (!favorite) {
                console.warn('Favorite record not found');
                return;
            }

            const deleteResponse = await fetch(`/api/favorites/${favorite.id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                }
            });

            if (deleteResponse.status === 204) {
                this.updateButtonState(button, false);
                this.showNotification('Удалено из избранного', 'info');
                
                // Если на странице избранного — удаляем карточку из DOM
                const card = button.closest('.favorite-item');
                if (card) {
                    card.remove();
                    this.updateFavoritesMap();
                }
            }
        } catch (error) {
            console.error('Error removing from favorites:', error);
            this.showNotification('Ошибка при удалении', 'error');
        }
    }

    updateButtonState(button, isFavorite) {
        const iconSpan = button.querySelector('.favorite-icon') || button;
        const textSpan = button.querySelector('.favorite-text');
        
        if (isFavorite) {
            button.classList.add('active', 'btn-danger');
            button.classList.remove('btn-outline-danger');
            iconSpan.innerHTML = '❤️';
            if (textSpan) textSpan.textContent = 'В избранном';
        } else {
            button.classList.remove('active', 'btn-danger');
            button.classList.add('btn-outline-danger');
            iconSpan.innerHTML = '🤍';
            if (textSpan) textSpan.textContent = 'В избранное';
        }
    }

    async loadFavoritesForMap() {
        const mapContainer = document.getElementById('favorites-map');
        if (!mapContainer) return;

        try {
            const response = await fetch('/api/favorites/');
            const favorites = await response.json();
            
            const stores = favorites.map(f => f.store_detail);
            
            // Инициализация карты с избранными магазинами
            this.initFavoritesMap(stores);
        } catch (error) {
            console.error('Error loading favorites:', error);
        }
    }

    initFavoritesMap(stores) {
        mapboxgl.accessToken = 'YOUR_MAPBOX_TOKEN'; // Замените на ваш токен
        
        const map = new mapboxgl.Map({
            container: 'favorites-map',
            style: 'mapbox://styles/mapbox/streets-v11',
            center: [30.3158, 59.9390], // Санкт-Петербург по умолчанию
            zoom: 11
        });

        const bounds = new mapboxgl.LngLatBounds();

        stores.forEach(store => {
            if (!store.location) return;
            
            const coordinates = store.location.coordinates;
            
            // Добавляем маркер
            new mapboxgl.Marker({ color: '#e74c3c' })
                .setLngLat(coordinates)
                .setPopup(new mapboxgl.Popup().setHTML(`
                    <h5>${store.name}</h5>
                    <p>${store.address}</p>
                    <span class="badge">${store.category_display}</span>
                `))
                .addTo(map);
            
            bounds.extend(coordinates);
        });

        if (stores.length > 0) {
            map.fitBounds(bounds, { padding: 50 });
        }
    }

    async renderFavoritesList() {
        const container = document.getElementById('favorites-list-container');
        if (!container) return;

        try {
            const response = await fetch('/api/favorites/');
            const favorites = await response.json();
            
            if (favorites.length === 0) {
                container.innerHTML = `
                    <div class="alert alert-info">
                        У вас пока нет избранных магазинов.
                        <a href="/">Перейти к поиску</a>
                    </div>
                `;
                return;
            }

            const html = favorites.map(fav => `
                <div class="favorite-item card mb-3" data-favorite-id="${fav.id}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h5 class="card-title">${fav.store_detail.name}</h5>
                                <p class="card-text text-muted">${fav.store_detail.address}</p>
                                <span class="badge bg-secondary">${fav.store_detail.category_display}</span>
                                <small class="text-muted d-block mt-2">
                                    Добавлено: ${new Date(fav.created_at).toLocaleDateString('ru-RU')}
                                </small>
                            </div>
                            <button class="favorite-btn btn btn-sm btn-danger active" data-store-id="${fav.store_detail.id}">
                                <span class="favorite-icon">❤️</span>
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
            
            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = '<div class="alert alert-danger">Ошибка загрузки избранного</div>';
        }
    }

    showNotification(message, type = 'info') {
        // Простая реализация, можно заменить на Bootstrap Toast
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
        notification.style.zIndex = '9999';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => notification.remove(), 3000);
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.favoritesManager = new FavoritesManager();
});