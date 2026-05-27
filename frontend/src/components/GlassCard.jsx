import React from "react";

const GlassCard = React.forwardRef(({ children, className = "" }, ref) => {
  return (
    <div ref={ref} className={`glass-card rounded-3xl p-6 md:p-7 ${className}`}>
      {children}
    </div>
  );
});

GlassCard.displayName = "GlassCard";

export default GlassCard;
