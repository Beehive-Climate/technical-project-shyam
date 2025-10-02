function Header() {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          padding: "0.8rem 1rem",
          background: "#ffcc33",
          borderBottom: "2px solid #e6b800",
        }}
      >
        <img
          src="https://images.squarespace-cdn.com/content/v1/66475b033b688f0e73998029/666d1c2f-60be-4574-8a68-1d38f592cf69/beehive_logo-removebg-preview.png?format=1500w"
          alt="Beehive Logo"
          style={{ height: "40px", marginRight: "10px" }}
        />
        <span style={{ fontWeight: "bold", fontSize: "1.2rem", color: "#333" }}>
          Beehive Climate Chat
        </span>
      </div>
    );
  }
  
  export default Header;
  