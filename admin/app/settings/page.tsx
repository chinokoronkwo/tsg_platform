"use client";

import { useState } from "react";
import { FormField } from "@/components/forms/form-field";

export default function SettingsPage() {
  const [siteName, setSiteName] = useState("Snob Group");
  const [description, setDescription] = useState("Premium wine experiences and education.");
  const [contactEmail, setContactEmail] = useState("contact@snobgroup.com");
  const [twitter, setTwitter] = useState("");
  const [instagram, setInstagram] = useState("");
  const [facebook, setFacebook] = useState("");

  return (
    <div>
      <h1 className="font-heading text-4xl text-white mb-8">Global Settings</h1>

      <div className="max-w-2xl space-y-8">
        <div className="bg-surface rounded-lg border border-cream/10 p-6">
          <h2 className="font-heading text-xl text-white mb-6">Site Information</h2>
          <div className="space-y-4">
            <FormField
              label="Site Name"
              name="siteName"
              value={siteName}
              onChange={(e) => setSiteName(e.target.value)}
            />
            <FormField
              label="Description"
              name="description"
              as="textarea"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
            <FormField
              label="Contact Email"
              name="contactEmail"
              type="email"
              value={contactEmail}
              onChange={(e) => setContactEmail(e.target.value)}
            />
          </div>
        </div>

        <div className="bg-surface rounded-lg border border-cream/10 p-6">
          <h2 className="font-heading text-xl text-white mb-6">Social Links</h2>
          <div className="space-y-4">
            <FormField
              label="Twitter / X"
              name="twitter"
              type="url"
              placeholder="https://twitter.com/..."
              value={twitter}
              onChange={(e) => setTwitter(e.target.value)}
            />
            <FormField
              label="Instagram"
              name="instagram"
              type="url"
              placeholder="https://instagram.com/..."
              value={instagram}
              onChange={(e) => setInstagram(e.target.value)}
            />
            <FormField
              label="Facebook"
              name="facebook"
              type="url"
              placeholder="https://facebook.com/..."
              value={facebook}
              onChange={(e) => setFacebook(e.target.value)}
            />
          </div>
        </div>

        <div className="flex gap-4">
          <button className="px-6 py-2.5 bg-secondary text-primary font-semibold rounded-lg hover:bg-secondary/90 transition-colors">
            Save Changes
          </button>
          <button className="px-6 py-2.5 bg-surface-2 border border-cream/10 text-cream rounded-lg hover:bg-cream/5 transition-colors">
            Cancel
          </button>
        </div>

        <div className="bg-surface rounded-lg border border-red-500/30 p-6">
          <h2 className="font-heading text-xl text-red-400 mb-2">Danger Zone</h2>
          <p className="text-cream/60 text-sm mb-4">
            Irreversible actions. Proceed with caution.
          </p>
          <div className="flex gap-4">
            <button className="px-4 py-2 border border-red-500/50 text-red-400 rounded-lg hover:bg-red-500/10 transition-colors">
              Reset All Settings
            </button>
            <button className="px-4 py-2 border border-red-500/50 text-red-400 rounded-lg hover:bg-red-500/10 transition-colors">
              Export Data
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
