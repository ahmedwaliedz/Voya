        (function() {
        // ===== MENU DATA =====
        const menuData = {
            voya: {
                name: "VOYA Coffee & Drinks",
                subtitle: "Specialty coffee culture, quality, everyday rituals",
                categories: [
                    { name: "Hot Coffee", products: [
                        {name:"Espresso Single",price:35},{name:"Espresso Double",price:45},{name:"Machiato Single",price:45},{name:"Machiato Double",price:50},{name:"Flat White",price:60},{name:"Cortado",price:60},{name:"Americano",price:60},{name:"Cappuccino",price:80},{name:"Latte",price:80},{name:"Turkish Coffee Single",price:25},{name:"Turkish Coffee Double",price:35}
                    ]},
                    { name: "Hot Beverage Flavour", products: [
                        {name:"Spanish Latte",price:100},{name:"White Mocha",price:100},{name:"Mocha Latte",price:100},{name:"Salted Caramel",price:100},{name:"Caramel Machiato",price:100},{name:"Peanut Latte",price:105},{name:"Pistachio Latte",price:105},{name:"Lotus Latte",price:105},{name:"Nutella Latte",price:105},{name:"French Coffee",price:40},{name:"Hazelnut Coffee",price:40}
                    ]},
                    { name: "Hot Beverage Without Coffee", products: [
                        {name:"Classic Matcha",price:105},{name:"White Matcha",price:105},{name:"Spanish Matcha",price:105},{name:"Hot Chocolate",price:90},{name:"White Hot Chocolate",price:90},{name:"Red Tea",price:25},{name:"Green Tea",price:25}
                    ]},
                    { name: "Cold Beverage Cubes", products: [
                        {name:"Ice Americano",price:60},{name:"Ice Latte",price:80},{name:"Ice Spanish",price:100},{name:"Ice Mocha",price:100},{name:"Ice White Mocha",price:100},{name:"Ice Caramel Machiato",price:100},{name:"Ice Salted Caramel",price:100},{name:"Ice Banana Coffee",price:100},{name:"Ice Vanilla Double Cream",price:105},{name:"Ice Pistachio Latte",price:105},{name:"Ice Nutella Latte",price:105}
                    ]},
                    { name: "Cold Beverage Milk Blend", products: [
                        {name:"Lotus Milkshake",price:70},{name:"Pistachio Milkshake",price:80},{name:"Nutella Milkshake",price:70},{name:"Blueberry Milkshake",price:70},{name:"Peach Milkshake",price:70},{name:"Chocolate Milkshake",price:70},{name:"Vanilla Milkshake",price:70},{name:"Caramel Milkshake",price:70}
                    ]},
                    { name: "Cold Beverage Frappe", products: [
                        {name:"Coffee Frappe",price:100},{name:"Caramel Frappe",price:105},{name:"Mocha Frappe",price:105},{name:"White Mocha Frappe",price:105},{name:"Spanish Frappe",price:105},{name:"Salted Caramel Frappe",price:105},{name:"Pistachio Frappe",price:105},{name:"Lotus Frappe",price:105},{name:"Nutella Frappe",price:105},{name:"Banana Coffee Frappe",price:105}
                    ]},
                    { name: "Other Drinks", products: [
                        {name:"Classic Energy",price:105},{name:"Coco Berry",price:105},{name:"Redbull Passion",price:105},{name:"Redbull Peach",price:105},{name:"Humer Head",price:70},{name:"Ice Cream 1 Scoop",price:20},{name:"Ice Cream 3 Scoop",price:50},{name:"Banana Split",price:70},{name:"Cola",price:30},{name:"Schweppes",price:30},{name:"V Cola",price:30},{name:"Small Water",price:10},{name:"Red Bull",price:70},{name:"Fayrouz",price:30},{name:"Birell",price:30}
                    ]},
                    { name: "Dessert", products: [
                        {name:"Cheese Cake",price:110},{name:"Tiramisu",price:110},{name:"Honey Cake",price:110},{name:"Brownies",price:80},{name:"Plain Croissant",price:60},{name:"Triple Chocolate",price:120},{name:"Chocolate Eclair",price:80},{name:"Pain Suisse Chocolate",price:80},{name:"Double Chocolate Cookies",price:70},{name:"Classic Cookies",price:70},{name:"Chocolate Muffin",price:80},{name:"Vanilla Muffin",price:80}
                    ]},
                    { name: "Mojito", products: [
                        {name:"Classic Mojito",price:80},{name:"Blueberry Mojito",price:80},{name:"Green Apple Mojito",price:80},{name:"Passion Mojito",price:80},{name:"Peach Mojito",price:80},{name:"Strawberry Mojito",price:80},{name:"Pineapple Strawberry Mojito",price:80},{name:"Raspberry Mojito",price:80}
                    ]},
                    { name: "Ice Tea", products: [
                        {name:"Peach Ice Tea",price:70},{name:"Blueberry Ice Tea",price:70},{name:"Green Apple Ice Tea",price:70}
                    ]},
                    { name: "Juice", products: [
                        {name:"Orange",price:60},{name:"Mango",price:60},{name:"Strawberry",price:60},{name:"Guava",price:60},{name:"Lemon Mint",price:50},{name:"Florida",price:70},{name:"Avocado",price:80},{name:"Kiwi",price:80}
                    ]},
                    { name: "Matcha", products: [
                        {name:"Ice Classic Matcha",price:105},{name:"Ice White Matcha",price:105},{name:"Ice Strawberry Matcha",price:105},{name:"Ice Spanish Matcha",price:105}
                    ]}
                ]
            },
            papa: {
                name: "Papa Voya",
                subtitle: "Balanced healthy dining, mindful food choices",
                categories: [
                    { name: "Main Dishes", products: [
                        {name:"Chicken Yogurt Salad",price:235,desc:"Lettuce, bell pepper, avocado, sweet corn, cherry tomatoes, red beans, red cabbage, grilled chicken, lemon dill sauce."},
                        {name:"Tuna Salad",price:310,desc:"Lettuce, red onion, cherry tomatoes, boiled potato cubes, boiled eggs, olive, tuna, honey coriander sauce."},
                        {name:"Quinoa Salad",price:270,desc:"Quinoa, lettuce, avocado, tomato, onion, orange, mango, coriander."},
                        {name:"Alfredo Pasta",price:250,desc:"Oat pasta, heavy cream, grilled bell pepper, parmesan cheese, grilled chicken."},
                        {name:"Beet Pasta",price:230,desc:"Oat pasta, parmesan cheese, grilled chicken, beetroot sauce."},
                        {name:"Protein Burger",price:230,desc:"Burger patty, egg, lettuce, brown toast, honey sauce. Served with side salad."},
                        {name:"Avocado Burger",price:240,desc:"Burger patty, lettuce, cherry tomatoes, cucumber, carrots, guacamole, cheese slices, honey sauce."},
                        {name:"Chicken Lemon",price:240,desc:"Grilled chicken breasts, olive oil, lemon sauce, onions, oregano. Served with side dish: mashed potatoes or white rice."},
                        {name:"Chicken Coconut",price:270,desc:"Grilled chicken breasts, coconut sauce. Served with side dish: mashed potatoes or white rice."}
                    ]}
                ]
            },
            mama: {
                name: "Mama Voya",
                subtitle: "Comfort food, indulgent dishes, familiar flavors",
                categories: [
                    { name: "Main Courses", note: "All main courses are served with two sides of sauteed vegetables, rice, or fries.", products: [
                        {name:"Grilled Chicken",price:240},{name:"Two Way Chicken",price:260},{name:"Cordon Bleu",price:270},{name:"Chicken Fajita",price:280},{name:"Beef Fillet",price:360},{name:"Beef Stroganoff",price:360}
                    ]},
                    { name: "Salads", products: [
                        {name:"Caesar Salad",price:110},{name:"Greek Salad",price:140},{name:"Chicken Caesar Salad",price:150},{name:"Waldorf Salad",price:240}
                    ]},
                    { name: "Pasta", products: [
                        {name:"Arrabbiata Pasta",price:140},{name:"Bolognese Pasta",price:160},{name:"Alfredo Pasta",price:190},{name:"Pesto Pasta",price:195},{name:"Negresco Pasta",price:220},{name:"Mac and Cheese Pasta",price:220},{name:"Steak Pasta",price:270}
                    ]},
                    { name: "Pizza", products: [
                        {name:"Margherita Pizza",price:130},{name:"Vegetable Pizza",price:180},{name:"Funghi Pizza",price:180},{name:"Quattro Pizza",price:190},{name:"Super Supreme Pizza",price:190},{name:"Pepperoni Pizza",price:195},{name:"BBQ Pizza",price:210},{name:"Ranch Pizza",price:220}
                    ]},
                    { name: "Cold Cuts", products: [
                        {name:"Turkey Sandwich",price:120},{name:"Bacon Cheese Sandwich",price:120},{name:"Pepperoni Cheese Sandwich",price:120},{name:"Club Sandwich",price:230}
                    ]},
                    { name: "Burger", products: [
                        {name:"Classic Burger",price:215},{name:"Voya Burger",price:250},{name:"Juicy Lucy",price:250},{name:"Mushroom Burger",price:260}
                    ]},
                    { name: "Sandwiches", products: [
                        {name:"Quesadilla Sandwich",price:155},{name:"Funghi Sandwich",price:155},{name:"Crispy Chicken Sandwich",price:165},{name:"Fried Chicken Sandwich",price:175}
                    ]}
                ]
            }
        };

        let cart = [];
        let currentBrand = 'voya';
        let currentCategoryIndex = 0;
        let currentProductIndex = 0;

        const brandInfo = {
            voya: {
                title: 'VOYA Room',
                subtitle: 'Specialty coffee for everyday rituals.',
                desc: 'Crafted cups, warm energy, and the small daily moments that turn into a trip.',
                fallbackDesc: 'A Voya favorite from the coffee room.'
            },
            papa: {
                title: 'Papa Voya Room',
                subtitle: 'Balanced plates, fresh energy, mindful choices.',
                desc: 'Healthy food with color, freshness, and enough comfort to keep it joyful.',
                fallbackDesc: 'A balanced choice from Papa Voya.'
            },
            mama: {
                title: 'Mama Voya Room',
                subtitle: 'Comfort classics made for sharing.',
                desc: 'Familiar flavors, generous plates, and the warm side of Voya House.',
                fallbackDesc: 'A comfort pick from Mama Voya.'
            }
        };

        // ===== PAGE LOAD =====
        function handlePageLoad() {
            const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            if (!reducedMotion) {
                const transition = document.getElementById('pageTransition');
                // Start exit animation shortly after load
                setTimeout(() => {
                    if (transition) transition.classList.add('is-exiting');
                }, 200);
                // Add is-loaded when hero animations should start (after transition exits)
                setTimeout(() => {
                    document.body.classList.add('is-loaded');
                }, 2000);
                // Remove transition element
                setTimeout(() => {
                    if (transition) transition.remove();
                }, 3200);
            } else {
                document.body.classList.add('is-loaded');
                const transition = document.getElementById('pageTransition');
                if (transition) transition.remove();
            }
        }
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            handlePageLoad();
        } else {
            window.addEventListener('load', handlePageLoad);
        }

        // ===== INIT =====
        document.addEventListener('DOMContentLoaded', () => {
            const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            if (!reducedMotion) {
                document.body.classList.add('motion-ready');
            }
            setupHeaderScroll();
            setupSmoothScroll();
            setupMobileMenu();
            setupScrollReveal();
            initMenu();
            updateCartUI();
            initRailDragScroll();
        });

        function initMenu() {
            currentBrand = 'voya';
            currentCategoryIndex = 0;
            currentProductIndex = 0;
            renderBrandSwitch();
            renderRoomIntro();
            renderCategoryChips();
            renderMenuContent();
        }

        function renderBrandSwitch() {
            const container = document.getElementById('brandSwitch');
            const brands = [
                { key: 'voya', name: 'VOYA', label: 'Coffee & Drinks' },
                { key: 'papa', name: 'Papa Voya', label: 'Healthy Food' },
                { key: 'mama', name: 'Mama Voya', label: 'Comfort Food' }
            ];
            container.innerHTML = brands.map(b => `
                <button type="button" class="brand-room brand-room--${b.key} stagger-item ${b.key === currentBrand ? 'active' : ''}"
                        onclick="switchBrand('${b.key}')"
                        aria-pressed="${b.key === currentBrand}">
                    <span class="brand-room-name">${b.name}</span>
                    <span class="brand-room-label">${b.label}</span>
                </button>
            `).join('');
            refreshRevealItems();
        }

        function renderRoomIntro() {
            const container = document.getElementById('roomIntro');
            const info = brandInfo[currentBrand];
            container.innerHTML = `
                <div class="room-intro room-intro--${currentBrand}">
                    <h3 class="room-intro-title">${info.title}</h3>
                    <p class="room-intro-subtitle">${info.subtitle}</p>
                    <p class="room-intro-desc">${info.desc}</p>
                </div>
            `;
        }

        function renderCategoryChips() {
            const container = document.getElementById('categoryChips');
            const data = menuData[currentBrand];
            if (!data) return;
            container.innerHTML = data.categories.map((cat, idx) => `
                <button type="button" class="category-chip stagger-item ${idx === currentCategoryIndex ? 'active' : ''}"
                        onclick="switchCategory(${idx})"
                        aria-pressed="${idx === currentCategoryIndex}">
                    ${cat.name} <span class="category-chip-count">${cat.products.length}</span>
                </button>
            `).join('');
            refreshRevealItems();
        }

        function renderMenuContent(preserveScroll = false) {
            const container = document.getElementById('menuContent');
            const data = menuData[currentBrand];
            if (!data) return;

            const category = data.categories[currentCategoryIndex];
            if (!category) return;

            const products = category.products;
            if (currentProductIndex >= products.length) currentProductIndex = 0;

            const oldRail = document.getElementById('productRail');
            const savedScroll = preserveScroll && oldRail ? oldRail.scrollLeft : 0;

            const railHtml = products.map((prod, idx) => {
                const ci = cart.find(i => i.name === prod.name);
                const qty = ci ? ci.qty : 0;
                const delay = idx * 60;
                return `
                    <div class="rail-card ${idx === currentProductIndex ? 'selected' : ''} is-entering" style="animation-delay: ${delay}ms" onclick="selectProduct(${idx})">
                        <div class="rail-card-name">${prod.name}</div>
                        ${prod.desc ? `<div class="rail-card-desc">${prod.desc}</div>` : ''}
                        <div class="rail-card-cat">${category.name}</div>
                        <div class="rail-card-bottom">
                            <div class="rail-card-price">${prod.price} <span style="font-size:0.6rem;font-weight:400;opacity:0.6">EGP</span></div>
                            ${qty > 0 ? `
                                <div class="rail-card-qty">
                                    <button type="button" class="rail-card-qty-btn" onclick="event.stopPropagation();updateQty('${prod.name}',-1)" aria-label="Decrease quantity">&minus;</button>
                                    <span class="rail-card-qty-val">${qty}</span>
                                    <button type="button" class="rail-card-qty-btn" onclick="event.stopPropagation();updateQty('${prod.name}',1)" aria-label="Increase quantity">+</button>
                                </div>
                            ` : `
                                <button type="button" class="rail-card-add" onclick="event.stopPropagation();addToCart('${prod.name}',${prod.price})" aria-label="Add ${prod.name}">+</button>
                            `}
                        </div>
                    </div>
                `;
            }).join('');

            container.innerHTML = `
                <div class="product-rail-section">
                    <div class="product-rail-header">
                        <div class="product-rail-title">${category.name} &middot; ${products.length} item${products.length !== 1 ? 's' : ''}</div>
                        <div class="product-rail-nav">
                            <button type="button" class="product-rail-btn" onclick="scrollRail(-1)" aria-label="Previous products">&lsaquo;</button>
                            <button type="button" class="product-rail-btn" onclick="scrollRail(1)" aria-label="Next products">&rsaquo;</button>
                        </div>
                    </div>
                    <div class="product-rail" id="productRail">${railHtml}</div>
                </div>
            `;

            if (preserveScroll) {
                const newRail = document.getElementById('productRail');
                if (newRail) newRail.scrollLeft = savedScroll;
            }

            refreshRevealItems();
        }

        function switchBrand(brand) {
            if (brand === currentBrand) return;
            currentBrand = brand;
            currentCategoryIndex = 0;
            currentProductIndex = 0;
            renderBrandSwitch();
            renderRoomIntro();
            renderCategoryChips();
            const chips = document.getElementById('categoryChips');
            if (chips) chips.scrollLeft = 0;
            renderMenuContent();
        }

        function switchCategory(idx) {
            currentCategoryIndex = idx;
            currentProductIndex = 0;
            renderCategoryChips();
            renderMenuContent();
            requestAnimationFrame(centerActiveCategoryChip);
        }

        function selectProduct(idx) {
            if (idx === currentProductIndex) return;
            currentProductIndex = idx;
            const rail = document.getElementById('productRail');
            if (!rail) return;
            rail.querySelectorAll('.rail-card').forEach((card, i) => {
                card.classList.toggle('selected', i === idx);
            });
        }

        function scrollRail(dir) {
            const rail = document.getElementById('productRail');
            const firstCard = rail ? rail.querySelector('.rail-card') : null;
            if (!rail || !firstCard) return;
            const styles = getComputedStyle(rail);
            const gap = parseFloat(styles.columnGap || styles.gap || 0);
            const amount = firstCard.offsetWidth + gap;
            rail.scrollBy({ left: dir * amount, behavior: 'smooth' });
        }

        function initRailDragScroll() {
            const rail = document.getElementById('productRail');
            if (!rail) return;
            let isDragging = false;
            let startX = 0;
            let scrollLeft = 0;

            rail.addEventListener('pointerdown', (e) => {
                if (e.pointerType === 'touch') return;
                isDragging = true;
                startX = e.pageX - rail.offsetLeft;
                scrollLeft = rail.scrollLeft;
                rail.style.cursor = 'grabbing';
                rail.setPointerCapture(e.pointerId);
            });

            rail.addEventListener('pointermove', (e) => {
                if (!isDragging) return;
                if (e.pointerType === 'touch') return;
                e.preventDefault();
                const x = e.pageX - rail.offsetLeft;
                const walk = (x - startX) * 1.5;
                rail.scrollLeft = scrollLeft - walk;
            });

            rail.addEventListener('pointerup', () => {
                isDragging = false;
                rail.style.cursor = '';
            });

            rail.addEventListener('pointercancel', () => {
                isDragging = false;
                rail.style.cursor = '';
            });
        }

        function scrollCategories(dir) {
            const chips = document.getElementById('categoryChips');
            if (!chips) return;
            chips.scrollBy({ left: dir * 240, behavior: 'smooth' });
        }

        function centerActiveCategoryChip() {
            const chips = document.getElementById('categoryChips');
            const active = chips?.querySelector('.category-chip.active');
            if (!chips || !active) return;
            const targetLeft = active.offsetLeft - (chips.clientWidth - active.offsetWidth) / 2;
            chips.scrollTo({
                left: Math.max(0, targetLeft),
                behavior: 'smooth'
            });
        }

        // Alias for backward compatibility with mood card buttons
        function switchToMenu(brand) {
            switchBrand(brand);
            document.getElementById('menu').scrollIntoView({ behavior: 'smooth' });
        }

        let revealObserver = null;
        let motionEnabled = true;

        function setupScrollReveal() {
            motionEnabled = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            if (!motionEnabled) {
                document.querySelectorAll('.reveal, .reveal-scale, .stagger-item, .reveal-mask, .text-reveal, .section-motion').forEach(el => {
                    el.classList.add('visible');
                });
                return;
            }
            if (revealObserver) {
                revealObserver.disconnect();
            }
            revealObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (!entry.isIntersecting) return;
                    const el = entry.target;
                    if (el.classList.contains('stagger-item')) {
                        const parent = el.parentElement;
                        const siblings = parent ? Array.from(parent.querySelectorAll('.stagger-item')) : [];
                        const idx = siblings.indexOf(el);
                        el.style.transitionDelay = `${Math.min(idx * 80, 450)}ms`;
                    }
                    el.classList.add('visible');
                    revealObserver.unobserve(el);
                });
            }, {
                threshold: 0.12,
                rootMargin: '0px 0px -8% 0px'
            });
            refreshRevealItems();
        }

        function refreshRevealItems(scope) {
            if (!motionEnabled) return;
            const target = scope || document;
            const items = target.querySelectorAll('.reveal:not(.visible), .reveal-scale:not(.visible), .stagger-item:not(.visible), .reveal-mask:not(.visible), .text-reveal:not(.visible), .section-motion:not(.visible)');
            items.forEach(item => {
                if (item.dataset.revealReady === 'true') return;
                item.dataset.revealReady = 'true';
                if (revealObserver) {
                    revealObserver.observe(item);
                }
            });
        }

        function setupHeaderScroll() {
            let ticking = false;
            const isMobile = () => window.innerWidth < 769;
            window.addEventListener('scroll', () => {
                document.getElementById('header').classList.toggle('scrolled', window.scrollY > 60);
                if (!ticking) {
                    requestAnimationFrame(() => {
                        if (!isMobile()) {
                            const y = window.scrollY;
                            document.documentElement.style.setProperty('--parallax-y', `${y * 0.08}px`);
                            document.documentElement.style.setProperty('--parallax-x', `${(window.innerWidth / 2 - window.scrollX) * 0.02}px`);
                        }
                        ticking = false;
                    });
                    ticking = true;
                }
            });
        }

        function setupSmoothScroll() {
            document.querySelectorAll('a[href^="#"]').forEach(a => {
                a.addEventListener('click', e => {
                    e.preventDefault();
                    const t = document.querySelector(a.getAttribute('href'));
                    if (t) t.scrollIntoView({ behavior: 'smooth' });
                    closeMobileMenu();
                });
            });
        }

        function setupMobileMenu() {
            const nav = document.getElementById('mobileNav');
            const btn = document.getElementById('mobileMenuBtn');
            if (!nav || !btn) return;
            btn.addEventListener('click', () => {
                const isOpen = nav.classList.toggle('open');
                btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            });
            nav.querySelectorAll('a').forEach(link => {
                link.addEventListener('click', () => {
                    nav.classList.remove('open');
                    btn.setAttribute('aria-expanded', 'false');
                });
            });
        }

        function closeMobileMenu() {
            const nav = document.getElementById('mobileNav');
            const btn = document.getElementById('mobileMenuBtn');
            if (!nav || !btn) return;
            nav.classList.remove('open');
            btn.setAttribute('aria-expanded', 'false');
        }

        // ===== CART =====
        function addToCart(name, price) {
            const existing = cart.find(i => i.name === name);
            if (existing) existing.qty++;
            else cart.push({ name, price, qty: 1 });
            updateCartUI();
            updateRailCards();
            showToast(`${name} added to cart`);
        }

        function updateQty(name, change) {
            const item = cart.find(i => i.name === name);
            if (item) {
                item.qty += change;
                if (item.qty <= 0) cart = cart.filter(i => i.name !== name);
            }
            updateCartUI();
            updateRailCards();
        }

        function updateRailCards() {
            const rail = document.getElementById('productRail');
            if (!rail) return;
            rail.querySelectorAll('.rail-card').forEach(card => {
                const name = card.querySelector('.rail-card-name')?.textContent;
                if (!name) return;
                const ci = cart.find(i => i.name === name);
                const qty = ci ? ci.qty : 0;
                const bottom = card.querySelector('.rail-card-bottom');
                if (!bottom) return;
                if (qty > 0) {
                    bottom.innerHTML = `
                        <div class="rail-card-price">${ci.price} <span style="font-size:0.6rem;font-weight:400;opacity:0.6">EGP</span></div>
                        <div class="rail-card-qty">
                            <button type="button" class="rail-card-qty-btn" onclick="event.stopPropagation();updateQty('${name}',-1)" aria-label="Decrease quantity">&minus;</button>
                            <span class="rail-card-qty-val">${qty}</span>
                            <button type="button" class="rail-card-qty-btn" onclick="event.stopPropagation();updateQty('${name}',1)" aria-label="Increase quantity">+</button>
                        </div>
                    `;
                } else {
                    const priceEl = card.querySelector('.rail-card-price');
                    const price = priceEl ? parseInt(priceEl.textContent) : 0;
                    bottom.innerHTML = `
                        <div class="rail-card-price">${price} <span style="font-size:0.6rem;font-weight:400;opacity:0.6">EGP</span></div>
                        <button type="button" class="rail-card-add" onclick="event.stopPropagation();addToCart('${name}',${price})" aria-label="Add ${name}">+</button>
                    `;
                }
            });
        }

        function removeFromCart(name) {
            cart = cart.filter(i => i.name !== name);
            updateCartUI();
            updateRailCards();
        }

        function updateCartUI() {
            const count = cart.reduce((s, i) => s + i.qty, 0);
            const total = cart.reduce((s, i) => s + i.price * i.qty, 0);
            document.getElementById('cartCount').textContent = count;
            document.getElementById('cartTotal').innerHTML = `${total} <span style="font-size:0.75rem">EGP</span>`;
            document.getElementById('whatsappBtn').disabled = cart.length === 0;

            const orderStrip = document.getElementById('orderStrip');
            const drawerOpen = document.getElementById('cartDrawer').classList.contains('open');
            if (count > 0 && !drawerOpen) {
                orderStrip.classList.add('show');
                document.body.classList.add('order-strip-visible');
                document.getElementById('orderStripCount').textContent = count + ' item' + (count !== 1 ? 's' : '');
                document.getElementById('orderStripTotal').innerHTML = total + ' <span>EGP</span>';
            } else {
                orderStrip.classList.remove('show');
                document.body.classList.remove('order-strip-visible');
            }

            const itemsEl = document.getElementById('cartItems');
            if (cart.length === 0) {
                itemsEl.innerHTML = '<div class="cart-empty"><div class="cart-empty-icon">&#9749;</div><div>Your cart is empty</div></div>';
            } else {
                itemsEl.innerHTML = cart.map(item => `<div class="cart-item">
                    <div class="cart-item-info">
                        <div class="cart-item-name">${item.name}</div>
                        <div class="cart-item-unit">${item.price} EGP each</div>
                        <div class="cart-item-controls">
                            <button class="cart-item-qty-btn" onclick="updateQty('${item.name}',-1)" aria-label="Decrease">&minus;</button>
                            <span class="cart-item-qty">${item.qty}</span>
                            <button class="cart-item-qty-btn" onclick="updateQty('${item.name}',1)" aria-label="Increase">+</button>
                            <button class="cart-item-remove" onclick="removeFromCart('${item.name}')">Remove</button>
                        </div>
                    </div>
                    <div class="cart-item-total">${item.price * item.qty} EGP</div>
                </div>`).join('');
            }
        }

        function trapFocus(e) {
            const drawer = document.getElementById('cartDrawer');
            if (!drawer.classList.contains('open')) return;
            const focusable = drawer.querySelectorAll('button:not([disabled]), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (focusable.length === 0) return;
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (e.key === 'Tab') {
                if (e.shiftKey && document.activeElement === first) {
                    e.preventDefault();
                    last.focus();
                } else if (!e.shiftKey && document.activeElement === last) {
                    e.preventDefault();
                    first.focus();
                }
            }
            if (e.key === 'Escape') {
                toggleCart();
            }
        }

        function toggleCart() {
            document.getElementById('cartOverlay').classList.toggle('open');
            document.getElementById('cartDrawer').classList.toggle('open');
            const drawerOpen = document.getElementById('cartDrawer').classList.contains('open');
            document.body.style.overflow = drawerOpen ? 'hidden' : '';
            if (drawerOpen) {
                document.addEventListener('keydown', trapFocus);
                document.getElementById('cartClose')?.focus();
            } else {
                document.removeEventListener('keydown', trapFocus);
            }
            const count = cart.reduce((s, i) => s + i.qty, 0);
            const orderStrip = document.getElementById('orderStrip');
            if (count > 0 && !drawerOpen) {
                orderStrip.classList.add('show');
            } else {
                orderStrip.classList.remove('show');
            }
        }

        function orderOnWhatsApp() {
            if (cart.length === 0) return;
            let msg = 'Hello Voya House, I want to order:\n\n';
            cart.forEach(i => msg += `${i.qty}x ${i.name} - ${i.price * i.qty} EGP\n`);
            const total = cart.reduce((s, i) => s + i.price * i.qty, 0);
            msg += `\nTotal: ${total} EGP`;
            window.open(`https://wa.me/201050000598?text=${encodeURIComponent(msg)}`, '_blank');
        }

        function showToast(msg) {
            const toast = document.getElementById('toast');
            toast.textContent = msg;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 2500);
        }

        // Expose functions used by inline onclick handlers
        window.toggleCart = toggleCart;
        window.switchBrand = switchBrand;
        window.switchCategory = switchCategory;
        window.selectProduct = selectProduct;
        window.scrollRail = scrollRail;
        window.updateQty = updateQty;
        window.addToCart = addToCart;
        window.removeFromCart = removeFromCart;
        window.orderOnWhatsApp = orderOnWhatsApp;
        window.switchToMenu = switchToMenu;
        })();
