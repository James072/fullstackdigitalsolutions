const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
        console.log(entry);
        if (entry.isIntersecting) {
            entry.target.classList.add("show");
        } else {
            entry.target.classList.remove("show");
        }
    });
});

const hiddenElements = document.querySelectorAll('.hidden-left, .hidden-right');
hiddenElements.forEach((el) => observer .observe(el)); 


// Initialize Stripe with your Test Publishable Key
const stripe = Stripe('pk_test_51ULIzeIjz4EbMsqXOP46LDxOmmZ8f4qCNWWF6i0UCKsoUkgAP95Q93FRkH5ixSKEhnFEovQhPNU8zIx4Bq3UKwqW006R6EkzZo'); 
const elements = stripe.elements();

// Create the card element with custom styling to match your dark theme
const cardElement = elements.create('card', {
    style: {
        base: {
            color: '#ffffff', // White text for the dark background
            fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
            fontSmoothing: 'antialiased',
            fontSize: '16px',
            '::placeholder': {
                color: '#aab7c4'
            }
        },
        invalid: {
            color: '#fa755a',
            iconColor: '#fa755a'
        }
    }
});

// Mount the element into the empty div in your HTML
cardElement.mount('#card-element');

const form = document.getElementById('consult-form');
const clientSecret = form.dataset.secret; // Extract the secret Flask injected

form.addEventListener('submit', async (event) => {
    // 1. Prevent the form from submitting immediately
    event.preventDefault();
    
    // Disable the submit button here if desired to prevent double-clicks
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;

    // 2. Send the card data securely to Stripe
    const {error, paymentIntent} = await stripe.confirmCardPayment(clientSecret, {
        payment_method: {
            card: cardElement,
            // You can also grab the name/email fields from your form and pass them here
            // billing_details: { name: document.getElementById('first_name').value }
        }
    });

    if (error) {
        // Show error to your customer (e.g., insufficient funds, card declined)
        document.getElementById('card-errors').textContent = error.message;

        // Re-enable the button so they can try again
        submitBtn.disabled = false;
    } else {
        // The payment has been processed!
        if (paymentIntent.status === 'succeeded') {
            // 3. Append the successful transaction ID to the form
            const hiddenInput = document.createElement('input');
            hiddenInput.setAttribute('type', 'hidden');
            hiddenInput.setAttribute('name', 'stripe_payment_id');
            hiddenInput.setAttribute('value', paymentIntent.id);
            form.appendChild(hiddenInput);

            // 4. Submit the rest of the data (and the file) to the Flask backend
            form.submit();
        }
    }
});