<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
	s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
	<!--:deploy:OHsentinel:/usr/local/share/OHsentinel/xsl:-->
	<xsl:output method="xml" encoding="utf-8" indent="yes" omit-xml-declaration="no"/>
	<xsl:param name="action" select="'create'"/>
	<xsl:param name="command" select="'Play'"/>
	<xsl:param name="namespace" select="'urn:av-openhome-org:service:Playlist:1'"/>
	<xsl:param name="argument" select="'Value'"/>
	<xsl:param name="value" select="'10'"/>
	<xsl:template match="/s:Envelope">
		<xsl:if test="$action = 'create'">
			<xsl:copy>
				<xsl:copy-of select="@*"/>
					<xsl:for-each select="s:Body">
					<xsl:copy>
						<xsl:element name="u:{$command}" namespace="{$namespace}">
						</xsl:element>
					</xsl:copy>
				</xsl:for-each>
			</xsl:copy>
		</xsl:if>
		<xsl:if test="$action = 'append'">
			<xsl:copy>
				<xsl:copy-of select="@*"/>
				<xsl:for-each select="s:Body">
					<xsl:copy>
						<xsl:for-each select="./*">
							<xsl:if test="local-name() = $command">
								<xsl:copy>
									<xsl:for-each select="./*">
										<xsl:copy>
											<xsl:value-of select="text()"/>
										</xsl:copy>
									</xsl:for-each>
									<xsl:element name="{$argument}">
										<xsl:value-of select="$value"/>
									</xsl:element>
								</xsl:copy>
							</xsl:if>
						</xsl:for-each>
					</xsl:copy>
				</xsl:for-each>
			</xsl:copy>
		</xsl:if>
	</xsl:template>
</xsl:stylesheet>
