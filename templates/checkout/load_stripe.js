// Set your publishable key (safe to expose)
const stripe = Stripe('pk_test_51Snz8ARyrKPZ9Ti4QneGnAHjdRCMQNxTB1ddd6p4UObMMAMH2o3ndikREik5NM9yEP8gKOlCtSyiaysqSB6xtnd900kaPmJUHv');

// Fetch the client secret from your backend endpoint (created in Part 2)
const response = await fetch("/create-payment-intent", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ items: [{ id: "prod_123", quantity: 1 }] }), // Example cart details
});

const { clientSecret } = await response.json();

const options = {
  clientSecret: clientSecret,
  // Optional: customize the appearance
  appearance: { /* ... */ },
};

// Set up Stripe.js and Elements
const elements = stripe.elements(options);
const paymentElement = elements.create('payment');
paymentElement.mount('#payment-element');

// server.js (or similar)
require('dotenv').config();
const express = require('express');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY); // Use your secret key
const app = express();

app.use(express.json());

// Define a map of store items with prices on the server (trusted environment)
const storeItems = new Map([
  ["prod_123", { price: 1099, name: "Gizmo" }],
  // ... other items
]);

app.post('/create-payment-intent', async (req, res) => {
  const { items } = req.body;

  // Calculate the total amount on the server
  const amount = items.reduce((sum, item) => {
    const storeItem = storeItems.get(item.id);
    return sum + storeItem.price * item.quantity;
  }, 0);

  try {
    // Create a PaymentIntent with the amount and currency
    const paymentIntent = await stripe.paymentIntents.create({
      amount: amount,
      currency: 'usd',
      automatic_payment_methods: { enabled: true }, // Let Stripe handle available payment methods
    });

    // Send the client secret back to the frontend
    res.status(200).send({
      clientSecret: paymentIntent.client_secret,
    });

  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(3000, () => console.log('Server running on port 3000'));

// frontend script
const form = document.getElementById('payment-form');

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const { error } = await stripe.confirmPayment({
    elements,
    confirmParams: {
      // Return URL where the user is redirected after the payment
      return_url: "https://",
    },
  });

  // Handle any errors that occur during confirmation
  if (error) {
    const messages = document.getElementById('error-message');
    messages.innerText = error.message;
  }
});
